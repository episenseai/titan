from .idp import IdP, OAuth2Provider, OAuth2LoginClient, OAuth2AuthClient
from urllib.parse import parse_qsl, urlencode
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
