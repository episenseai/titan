from ..auth.github import GithubAuthClient, GithubLoginClient
from ..auth.google import GoogleAuthClient, GoogleLoginClient
from .oauth2 import get_oauth2_settings

github_login_client: GithubLoginClient = GithubLoginClient.new(
    client_id=get_oauth2_settings().github_client_id,
    scope=get_oauth2_settings().github_client_scope,
    redirect_uri=get_oauth2_settings().github_redirect_uri,
)

github_auth_client: GithubAuthClient = GithubAuthClient.new(
    client_id=get_oauth2_settings().github_client_id,
    scope=get_oauth2_settings().github_client_scope,
    redirect_uri=get_oauth2_settings().github_redirect_uri,
    client_secret=get_oauth2_settings().github_client_secret,
)

google_login_client: GoogleLoginClient = GoogleLoginClient.new(
    client_id=get_oauth2_settings().google_client_id,
    scope=get_oauth2_settings().google_client_scope,
    redirect_uri=get_oauth2_settings().google_redirect_uri,
    iss=get_oauth2_settings().google_client_iss,
)

google_auth_client: GoogleAuthClient = GoogleAuthClient.new(
    client_id=get_oauth2_settings().google_client_id,
    scope=get_oauth2_settings().google_client_scope,
    redirect_uri=get_oauth2_settings().google_redirect_uri,
    client_secret=get_oauth2_settings().google_client_secret,
    iss=get_oauth2_settings().google_client_iss,
)
