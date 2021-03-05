from types import Union
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

from pydantic import AnyHttpUrl, SecretStr

from .models import IdP, OAuth2AuthClient, OAuth2LoginClient, OAuth2TokenGrant
from .state import StateToken

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


class GoogleLoginClient(OAuth2LoginClient):
    @staticmethod
    def new(
        client_id: str,
        scope: str,
        redirect_uri: Union[AnyHttpUrl, str],
    ) -> OAuth2LoginClient:
        """
        Builder method to create an instance of the class
        """
        return GoogleLoginClient(
            auth_url=GOOGLE_AUTH_URL,
            token_url=GOOGLE_TOKEN_URL,
            client_id=client_id,
            scope=scope,
            redirect_uri=redirect_uri,
        )

    @property
    def idp(self) -> IdP:
        return IdP.google

    def get_query_params(self, token: StateToken, refresh_token: bool = False) -> Dict[str, Any]:
        if refresh_token:
            access_type = "offline"
        else:
            access_type = "online"
        url_params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.scope,
            "access_type": access_type,
            "state": token.state,
        }
        print(f"{url_params=}")
        return url_params

    def get_urlencoded_query_params(self, token: StateToken, refresh_token: bool) -> str:
        return urlencode(self.get_query_params(token, refresh_token))

    def create_auth_url(self, token: StateToken, refresh_token: bool = False) -> str:
        encoded_params = self.get_urlencoded_query_params(token, refresh_token)
        return f"{str(self.auth_url)}?{encoded_params}"


class GoogleAuthClient(OAuth2AuthClient):
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
        return GoogleAuthClient(
            auth_url=GOOGLE_AUTH_URL,
            token_url=GOOGLE_TOKEN_URL,
            client_id=client_id,
            scope=scope,
            redirect_uri=redirect_uri,
            client_secret=client_secret,
        )

    @property
    def idp(self) -> IdP:
        return IdP.github

    def get_query_params(self, code: str, token: StateToken) -> Dict[str, Any]:
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
        pass

    def get_email_str(self, user_dict: Dict[str, Any]) -> str:
        raise NotImplementedError()

    def get_provider_id(self, user_dict: Dict[str, Any]) -> Optional[Union[str, int]]:
        raise NotImplementedError()
