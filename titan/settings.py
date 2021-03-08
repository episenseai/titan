from functools import lru_cache

from pydantic import SecretStr

from .models import ImmutBaseModel

AUTH_REDIRECT_URI = "http://localhost:8000/auth"

GITHUB_CLIENT_SCOPE = "user:email"
### GET THESE FROM THE **ENV***
GITHUB_CLIENT_ID = "5ffe8fd42976c5f477e3"
GITHUB_CLIENT_SECRET = "d6d6dc23b03f3b53a3d471ae02acd76c3e893ded"


GOOGLE_CLIENT_SCOPE = (
    "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile"
)
### GET THESE FROM THE **ENV***
GOOGLE_CLIENT_ID = "483992959077-cdtsj48dhnt87mjlbn6jlt707ls2st2p.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "WmUcqKFLcbiYSqghIIuUi4Hb"
# 'iss' claim in the JWT id_token from google
GOOGLE_CLIENT_ISS = "https://accounts.google.com"


class OAuth2Settings(ImmutBaseModel):
    # github client app settings
    github_client_id: str = GITHUB_CLIENT_ID
    github_client_scope: str = GITHUB_CLIENT_SCOPE
    github_redirect_uri: str = AUTH_REDIRECT_URI
    github_client_secret: SecretStr = GITHUB_CLIENT_SECRET
    # google client app settings
    google_client_id: str = GOOGLE_CLIENT_ID
    google_client_iss: str = GOOGLE_CLIENT_ISS
    google_client_scope: str = GOOGLE_CLIENT_SCOPE
    google_redirect_uri: str = AUTH_REDIRECT_URI
    google_client_secret: SecretStr = GOOGLE_CLIENT_SECRET


@lru_cache
def get_oauth2_settings() -> OAuth2Settings:
    return OAuth2Settings()


get_oauth2_settings()
