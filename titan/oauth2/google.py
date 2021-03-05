from .abc_client import OAuth2AuthClient, OAuth2LoginClient
from .models import IdP, OAuth2Provider, OAuth2TokenGrant
from urllib.parse import urlencode
from pydantic import AnyHttpUrl
from .state import StateToken


class GoogleLoginClient(OAuth2Provider, OAuth2LoginClient):
    client_id: str
    scope: str
    redirect_uri: AnyHttpUrl

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
