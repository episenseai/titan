from typing import Any, Optional, Union
from urllib.parse import urlencode

import httpx
from pydantic import AnyHttpUrl, SecretStr

from ..exceptions.exc import Oauth2AuthError, OAuth2EmailPrivdedError
from ..logger import logger
from .models import IdentityProvider, OAuth2AuthClient, OAuth2AuthentcatedUser, OAuth2LoginClient
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
    def idp(self) -> IdentityProvider:
        print("git idp")
        return IdentityProvider.github

    def get_query_params(self, token: StateToken, refresh_token: bool) -> dict[str, Any]:
        if refresh_token:
            raise ValueError("Github does not support refresh tokens")
        url_params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "state": token.state,
        }
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
    def idp(self) -> IdentityProvider:
        return IdentityProvider.github

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
    def validate_requested_scope(self, granted_scope: Union[str, list[str]]) -> tuple[bool, str]:
        missing_scope = []
        if isinstance(granted_scope, str):
            granted_scope = granted_scope.split(",")
        for scope in self.requested_scope():
            if scope not in granted_scope:
                if scope in ("read:user", "user:email", "user:follow"):
                    if "user" not in granted_scope:
                        missing_scope.append(scope)
        if not missing_scope:
            return (True, "")
        return (False, " ".join(missing_scope))

    async def authorize(self, code: str, token: StateToken) -> OAuth2AuthentcatedUser:
        async with httpx.AsyncClient() as client:
            try:
                params = self.get_query_params(code, token)
                headers = {"Accept": "application/json"}
                response = await client.post(str(self.token_url), params=params, headers=headers)
                response.raise_for_status()
            except httpx.RequestError as exc:
                err_msg = f"Github auth endpoint: {exc}"
                logger.error(err_msg)
                raise Oauth2AuthError(err_msg) from exc
            except Exception as exc:
                # This exception includes status_code != 200 error
                err_msg = f"Github auth endpoint: {response.status_code=} {exc=}"
                logger.error(err_msg)
                raise Oauth2AuthError(err_msg) from exc

            try:
                auth_dict: dict = response.json()
            except Exception as exc:
                err_msg = "Github auth JSON response decode: {exc}"
                logger.exception(err_msg)
                raise Oauth2AuthError(err_msg) from exc

            for key in ("access_token", "token_type", "scope"):
                if key not in auth_dict:
                    err_msg = f"Github auth response: missing ({key=})"
                    logger.error(err_msg)
                    raise Oauth2AuthError(err_msg)

            token_type: str = auth_dict.get("token_type")
            if not token_type or token_type.lower() != "bearer":
                # Sanity check
                err_msg = f"Github auth endpoint: ({token_type=}) != Bearer"
                logger.error(err_msg)
                raise Oauth2AuthError(err_msg)

            ok, missing_scope = self.validate_requested_scope(auth_dict.get("scope"))
            if not ok:
                err_msg = f"Github missing scope: ({missing_scope=})"
                logger.error(err_msg)
                raise Oauth2AuthError(err_msg)

            # Call the user info endpoint
            try:
                headers = {
                    "Authorization": f"token {auth_dict.get('access_token')}",
                    "Accept": "application/vnd.github.v3+json",
                }
                user_response = await client.get(GITHUB_USER_URL, headers=headers)
                user_response.raise_for_status()
            except httpx.RequestError as exc:
                err_msg = f"Github user info endpoint: {exc}"
                logger.error(err_msg)
                raise Oauth2AuthError(err_msg) from exc
            except httpx.HTTPStatusError as exc:
                err_msg = f"Github user info endpoint: {response.status_code=} {exc}"
                logger.error(err_msg)
                raise Oauth2AuthError(err_msg) from exc

            try:
                user_dict: dict = user_response.json()
            except Exception as exc:
                err_msg = f"Github user info JSON decode: {user_response=} {exc}"
                logger.error(err_msg)
                raise Oauth2AuthError(err_msg) from exc

            # Call the emails endpoint to get the primary email address.
            try:
                emails_response = await client.get(GITHUB_EMAILS_URL, headers=headers)
                emails_response.raise_for_status()
            except httpx.RequestError as exc:
                err_msg = f"Github emails endpoint: {exc} {exc.request}"
                logger.error(err_msg)
                raise Oauth2AuthError(err_msg) from exc
            except httpx.HTTPStatusError as exc:
                err_msg = f"Github emails endpoint: {response.status_code=} {exc=}"
                logger.error(err_msg)
                raise Oauth2AuthError(err_msg) from exc

            try:
                user_emails: dict = emails_response.json()
            except Exception as exc:
                err_msg = f"Github emails endpoint JSON decode: {emails_response=}"
                logger.error(err_msg)
                raise Oauth2AuthError(err_msg) from exc

            email_dict = next(
                filter(lambda x: isinstance(x, dict) and x.get("primary", False), user_emails),
                None,
            )
            primary_email = user_emails and email_dict.get("email", None)

            # This should not happen
            if primary_email is None or primary_email == "":
                logger.error(f"Github primary email: {email_dict=}")
                raise OAuth2EmailPrivdedError("Github primary email not found")

            if user_emails[0].get("verified", False) is not True:
                err_msg = "Github primary email not verified"
                logger.error(err_msg)
                raise OAuth2EmailPrivdedError(err_msg)

            user_dict.update({"provider_email": primary_email})

            return self.user(user_dict, auth_dict)

    def user(self, user_dict: dict, auth_dict: dict) -> OAuth2AuthentcatedUser:
        for key in ("id", "login", "email"):
            if key not in user_dict:
                err_msg = f"Github user create: missing {key=} in ({user_dict=}, {auth_dict=})"
                logger.error(err_msg)
                raise Oauth2AuthError(err_msg)

        return OAuth2AuthentcatedUser(
            email=user_dict["provider_email"],
            full_name=user_dict.get("name", None),
            picture=user_dict.get("avatar_url", ""),
            idp=self.idp,
            idp_userid=user_dict["id"],
            idp_username=user_dict["login"],
            provider_creds=auth_dict,
        )
