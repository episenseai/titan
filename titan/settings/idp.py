from ..auth.github import GithubAuthClient, GithubLoginClient
from ..auth.google import GoogleAuthClient, GoogleLoginClient
from .env import env

AUTH_REDIRECT_URI = f"http://localhost:{env().PORT}/auth"

GITHUB_CLIENT_SCOPE = "read:user user:email"

GOOGLE_CLIENT_SCOPE = "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile"
# 'iss' claim in the JWT id_token from google
GOOGLE_CLIENT_ISS = "https://accounts.google.com"

github_login_client: GithubLoginClient = GithubLoginClient.new(
    client_id=env().GITHUB_CLIENT_ID,
    scope=GITHUB_CLIENT_SCOPE,
    redirect_uri=AUTH_REDIRECT_URI,
)

github_auth_client: GithubAuthClient = GithubAuthClient.new(
    client_id=env().GITHUB_CLIENT_ID,
    scope=GITHUB_CLIENT_SCOPE,
    redirect_uri=AUTH_REDIRECT_URI,
    client_secret=env().GITHUB_CLIENT_SECRET.get_secret_value(),
)

google_login_client: GoogleLoginClient = GoogleLoginClient.new(
    client_id=env().GOOGLE_CLIENT_ID,
    scope=GOOGLE_CLIENT_SCOPE,
    redirect_uri=AUTH_REDIRECT_URI,
    iss=GOOGLE_CLIENT_ISS,
)

google_auth_client: GoogleAuthClient = GoogleAuthClient.new(
    client_id=env().GOOGLE_CLIENT_ID,
    scope=GOOGLE_CLIENT_SCOPE,
    redirect_uri=AUTH_REDIRECT_URI,
    iss=GOOGLE_CLIENT_ISS,
    client_secret=env().GOOGLE_CLIENT_SECRET.get_secret_value(),
)
