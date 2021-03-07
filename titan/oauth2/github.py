from typing import Any, Dict, Optional, Tuple, Union, List
from urllib.parse import urlencode

import httpx
from devtools import debug
from pydantic import AnyHttpUrl, SecretStr

from ..exceptions import (
    JSONDecodeError,
    Oauth2AuthorizationError,
    OAuth2MissingScope,
    OAuth2EmailPrivdedError,
    OAuth2MissingInfo,
)
from .models import IdP, OAuth2AuthClient, OAuth2LoginClient, OAuth2AuthentcatedUser
from .state import StateToken

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"

GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


class GithubLoginClient(OAuth2LoginClient):
    @staticmethod
    def new(
        client_id: str,
        scope: str,
        redirect_uri: Union[AnyHttpUrl, str],
        iss: Optional[str] = None,
    ) -> OAuth2LoginClient:
        """
        Builder method to create an instance of the class
        """
        return GithubLoginClient(
            auth_url=GITHUB_AUTH_URL,
            token_url=GITHUB_TOKEN_URL,
            client_id=client_id,
            scope=scope,
            redirect_uri=redirect_uri,
            iss=iss,
        )

    @property
    def idp(self) -> IdP:
        print("git idp")
        return IdP.github

    def get_query_params(self, token: StateToken, refresh_token: bool) -> Dict[str, Any]:
        if refresh_token:
            raise ValueError("Github does not support refresh tokens")
        url_params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "state": token.state,
        }
        print(f"{url_params=}")
        return url_params

    def get_urlencoded_query_params(self, token: StateToken, refresh_token: bool) -> str:
        return urlencode(self.get_query_params(token, refresh_token))

    def create_auth_url(self, token: StateToken, refresh_token: bool = False) -> str:
        encoded_params = self.get_urlencoded_query_params(token, refresh_token)
        return f"{str(self.auth_url)}?{encoded_params}"


class GithubAuthClient(OAuth2AuthClient):
    @staticmethod
    def new(
        client_id: str,
        scope: str,
        redirect_uri: Union[AnyHttpUrl, str],
        client_secret: Union[SecretStr, str],
        iss: Optional[str] = None,
    ) -> OAuth2AuthClient:
        """
        Builder method to create an instance of the class
        """
        return GithubAuthClient(
            auth_url=GITHUB_AUTH_URL,
            token_url=GITHUB_TOKEN_URL,
            user_url=GITHUB_USER_URL,
            client_id=client_id,
            scope=scope,
            redirect_uri=redirect_uri,
            client_secret=client_secret,
            iss=iss,
        )

    @property
    def idp(self) -> IdP:
        return IdP.github

    def get_query_params(self, code: str, token: StateToken) -> str:
        url_params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret.get_secret_value(),
            "code": code,
            "state": token.state,
        }
        return url_params

    def get_urlencoded_query_params(self, code: str, token: StateToken) -> str:
        return urlencode(self.get_query_params(code, token))

    # https://docs.github.com/en/developers/apps/scopes-for-oauth-apps#normalized-scopes
    def validate_requested_scope(self, granted_scope: Union[str, List[str]]) -> Tuple[bool, str]:
        missing_scope = []
        if isinstance(granted_scope, str):
            granted_scope = granted_scope.split()
        for scope in self.requested_scope():
            if scope not in granted_scope:
                if scope in ("read:user", "user:email", "user:follow"):
                    if "user" not in granted_scope:
                        missing_scope.append(scope)
        if len(missing_scope) == 0:
            return (True, "")
        return (False, " ".join(missing_scope))

    async def authorize(self, code: str, token: StateToken) -> OAuth2AuthentcatedUser:
        async with httpx.AsyncClient() as client:
            try:
                params = self.get_query_params(code, token)
                headers = {"Accept": "application/json"}
                response = await client.post(str(self.token_url), params=params, headers=headers)
                debug(response)
                response.raise_for_status()
            except httpx.RequestError as exc:
                raise Oauth2AuthorizationError(f"Resquest Error for token from github {exc.request}") from exc
            except Exception as exc:
                raise Oauth2AuthorizationError(
                    f"Response code != 20x for token request from github {exc.response}"
                ) from exc

            try:
                auth_dict: dict = response.json()
                debug(auth_dict)
                debug(auth_dict)
            except Exception as exc:
                raise JSONDecodeError("Error decoding token reponse (JSON) from github") from exc

            for key in ("access_token", "token_type", "scope"):
                if key not in auth_dict:
                    raise Oauth2AuthorizationError(f"Missing '{key}' in token reponse from github")

            token_type: str = auth_dict.get("token_type")
            if not token_type or token_type.lower() != "bearer":
                raise Oauth2AuthorizationError(f"{token_type=} != 'bearer' for token response from github")

            ok, missing_scope = self.validate_requested_scope(auth_dict.get("scope"))
            if not ok:
                raise OAuth2MissingScope(f"Scope mising from github auth {missing_scope=}")

            headers = {
                "Authorization": f"token {auth_dict.get('access_token')}",
                "Accept": "application/vnd.github.v3+json",
            }

            # call the user info endpoint
            try:
                user_response = await client.get(GITHUB_USER_URL, headers=headers)
                user_response.raise_for_status()
            except httpx.RequestError as exc:
                raise Oauth2AuthorizationError(f"Resquest Error for user info from github {exc.request}") from exc
            except httpx.HTTPStatusError as exc:
                raise Oauth2AuthorizationError(
                    f"Response code != 20x for user info from github {exc.response}"
                ) from exc

            try:
                user_dict: dict = user_response.json()
                debug(user_dict)
            except Exception as exc:
                raise JSONDecodeError("Error decoding user info reponse (JSON) from github") from exc

            # call the user/emails endpoint
            try:
                emails_response = await client.get(GITHUB_EMAILS_URL, headers=headers)
                emails_response.raise_for_status()
            except httpx.RequestError as exc:
                raise Oauth2AuthorizationError(f"Resquest Error for user info from github {exc.request}") from exc
            except httpx.HTTPStatusError as exc:
                raise Oauth2AuthorizationError(
                    f"Response code != 20x for user info from github {exc.response}"
                ) from exc

            try:
                user_emails: dict = emails_response.json()
                debug(user_emails)
            except Exception as exc:
                raise JSONDecodeError("Error decoding user info reponse (JSON) from github") from exc

            email_dict = next(
                filter(lambda x: isinstance(x, dict) and x.get("primary", False), user_emails),
                None,
            )
            primary_email = user_emails and email_dict.get("email", None)

            # some more verifications of the email can be done
            if primary_email is None or primary_email == "":
                raise OAuth2EmailPrivdedError("No primary email found associated wth github account")

            if user_emails[0].get("verified", False) is not True:
                raise OAuth2EmailPrivdedError(
                    "Your primary github email='{primary_email}' is not verified. Verify an try again."
                )

            user_dict.update({"provider_email": primary_email})

            return self.user(user_dict, auth_dict)

    def user(self, user_dict: dict, auth_dict: dict) -> OAuth2AuthentcatedUser:
        for key in ("id", "login", "email"):
            if key not in user_dict:
                raise OAuth2MissingInfo(f"Missing {key=} for user info during github auth")

        return OAuth2AuthentcatedUser(
            idp=IdP.github,
            provider_id=user_dict["id"],
            provider_email=user_dict["provider_email"],
            provider_username=user_dict["login"],
            avatar_url=user_dict.get("avatar_url", ""),
            full_name=user_dict.get("name", ""),
            provider_creds=auth_dict,
        )
