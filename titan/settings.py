from functools import lru_cache
from .model import ImmutBaseModel
from pydantic import SecretStr

AUTH_REDIRECT_URI = "http://localhost:8000/authorize"

GITHUB_CLIENT_ID = "5ffe8fd42976c5f477e3"
GITHUB_CLIENT_SECRET = "d6d6dc23b03f3b53a3d471ae02acd76c3e893ded"

GOOGLE_CLIENT_ID = "483992959077-cdtsj48dhnt87mjlbn6jlt707ls2st2p.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "WmUcqKFLcbiYSqghIIuUi4Hb"


class __OAuth2Settings(ImmutBaseModel):
    github_client_id: str = GITHUB_CLIENT_ID
    github_client_secret: SecretStr = GITHUB_CLIENT_SECRET
    github_redirect_uri: str = AUTH_REDIRECT_URI
    google_client_id: str = GOOGLE_CLIENT_ID
    google_client_secret: SecretStr = GOOGLE_CLIENT_SECRET
    google_redirect_uri: str = AUTH_REDIRECT_URI


@lru_cache
def get_oauth2_config() -> __OAuth2Settings:
    return __OAuth2Settings()


get_oauth2_config()
