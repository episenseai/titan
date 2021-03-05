from types import Union
from urllib.parse import urlencode

from pydantic import AnyHttpUrl

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

    def create_auth_url(self, token: StateToken) -> str:
        url_params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
            "state": token.state,
        }
        encoded_params = urlencode(url_params)
        return f"{str(self.auth_url)}?{encoded_params}"
