from typing import Any, Dict, Optional, Tuple, Union
from urllib.parse import urlencode

import httpx
from devtools import debug
from pydantic import AnyHttpUrl, SecretStr

from ..exceptions import JSONDecodeError, Oauth2AuthorizationError
from .models import IdP, OAuth2AuthClient, OAuth2LoginClient, OAuth2TokenGrant
from .state import StateToken

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


class GithubLoginClient(OAuth2LoginClient):
    @staticmethod
    def new(
        client_id: str,
        scope: str,
        redirect_uri: Union[AnyHttpUrl, str],
    ) -> OAuth2LoginClient:
        """
        Builder method to create an instance of the class
        """
        return GithubLoginClient(
            auth_url=GITHUB_AUTH_URL,
            token_url=GITHUB_TOKEN_URL,
            user_url=GITHUB_USER_URL,
            client_id=client_id,
            scope=scope,
            redirect_uri=redirect_uri,
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

    async def authorize(self, code: str, token: StateToken) -> Tuple[OAuth2TokenGrant, Dict[str, Any]]:
        params = self.get_query_params(code, token)
        headers = {"Accept": "application/json"}
        async with httpx.AsyncClient() as client:
            try:
                print("-------------------------")
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
                auth_response: dict = response.json()
                debug(auth_response)
            except Exception as exc:
                raise JSONDecodeError("Error decoding token reponse (JSON) from github") from exc

            for key in ("access_token", "token_type"):
                if key not in auth_response:
                    raise Oauth2AuthorizationError(f"Missing '{key}' in token reponse from github")

            # response also contains "scope"; we are ignoring that for now
            access_token: str = auth_response.get("access_token")
            token_type: str = auth_response.get("token_type")

            if not token_type or token_type.lower() != "bearer":
                raise Oauth2AuthorizationError(f"{token_type=} != 'bearer' for token response from github")

            # get user info using the access_token
            headers = {"Authorization": f"token {access_token}"}

            try:
                response = await client.get(str(self.user_url), headers=headers)
                response.raise_for_status()
            except httpx.RequestError as exc:
                raise Oauth2AuthorizationError(f"Resquest Error for user info from github {exc.request}") from exc
            except httpx.HTTPStatusError as exc:
                raise Oauth2AuthorizationError(
                    f"Response code != 20x for user info from github {exc.response}"
                ) from exc

            try:
                user_response: dict = response.json()
            except Exception as exc:
                raise JSONDecodeError("Error decoding user info reponse (JSON) from github") from exc

            return (
                OAuth2TokenGrant(access_token=access_token, token_type=token_type),
                user_response,
            )

    def get_email_str(self, user_dict: Dict[str, Any]) -> str:
        """
        user_dict: It's the same dict that is returned by the `authorize` function
        """
        email = user_dict.get("email", None)
        if email and isinstance(email, str) and len(email) >= 3:
            return email
        return None

    def get_provider_id(self, user_dict: Dict[str, Any]) -> Optional[Union[str, int]]:
        """
        user_dict: It's the same dict that is returned by the `authorize` function
        """
        provider_id = user_dict.get("id", None)
        if id and isinstance(id, (str, int)):
            return provider_id
        return None
