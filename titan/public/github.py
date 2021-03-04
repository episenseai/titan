from .idp import IdP, OAuth2Provider, OAuth2LoginClient, OAuth2AuthClient, OAuth2TokenGrant
from ..exceptions import JSONDecodeError, Oauth2AuthorizationError
import httpx
from typing import Tuple, Dict, Any, Optional, Union
from urllib.parse import urlencode
from pydantic import AnyHttpUrl, SecretStr
from .state import StateToken


class GithubLoginClient(OAuth2Provider, OAuth2LoginClient):
    client_id: str
    scope: str
    redirect_uri: AnyHttpUrl

    @property
    def idp(self) -> IdP:
        return IdP.github

    def create_auth_url(self, token: StateToken) -> str:
        url_params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "state": token.state,
        }
        encoded_params = urlencode(url_params)
        return f"{str(self.auth_url)}?{encoded_params}"


class GithubAuthClient(OAuth2Provider, OAuth2AuthClient):
    client_id: str
    client_secret: SecretStr
    user_url: AnyHttpUrl

    @property
    def idp(self) -> IdP:
        return IdP.github

    def get_query_params(self, code: str, state: str) -> str:
        url_params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret.get_secret_value(),
            "code": code,
            "state": state,
        }
        return url_params

    async def authorize(self, code: str, state: str) -> Tuple[OAuth2TokenGrant, Dict[str, Any]]:
        params = self.get_query_params(code, state)
        headers = {"Accept": "application/json"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(str(self.token_url), params=params, headers=headers)
                response.raise_for_status()
            except httpx.RequestError as ex:
                raise Oauth2AuthorizationError("Resquest Error for token from github") from ex
            except httpx.HTTPStatusError as ex:
                raise Oauth2AuthorizationError("Response code != 20x for token request from github") from ex

            try:
                auth_response: dict = response.json()
            except Exception as ex:
                raise JSONDecodeError("Error decoding token reponse (JSON) from github") from ex

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
            except httpx.RequestError as ex:
                raise Oauth2AuthorizationError("Resquest Error for user info from github") from ex
            except httpx.HTTPStatusError as ex:
                raise Oauth2AuthorizationError("Response code != 20x for user info from github") from ex

            try:
                user_response: dict = response.json()
            except Exception as ex:
                raise JSONDecodeError("Error decoding user info reponse (JSON) from github") from ex

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
        uid = user_dict.get("id", None)
        if id and isinstance(id, (str, int)):
            return uid
        return None
