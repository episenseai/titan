from typing import Optional
from uuid import uuid4

import httpx
from devtools import debug
from fastapi import APIRouter, Query, Request, status, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse

from ..tokens.jwt import AccessRefreshToken, TokenClaims
from .state import StateTokenDB, StateToken
from .idp import IdP, OAuth2AuthClient, OAuth2LoginClient, Oauth2ClientRegistry
from .github import GithubLoginClient, GithubAuthClient
from ..settings import get_oauth2_config
from ..accounts.user import UserDB

auth_router = APIRouter()
fake_user_db = UserDB()
state_token_db = StateTokenDB()
login_client_registry = Oauth2ClientRegistry(OAuth2LoginClient)
auth_client_registry = Oauth2ClientRegistry(OAuth2AuthClient)

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_SCOPE = "user:email"
GITHUB_USER_URL = "https://api.github.com/user"


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_SCOPE = "openid profile email"


login_client_registry.add(
    GithubLoginClient(
        auth_url=GITHUB_AUTH_URL,
        token_url=GITHUB_TOKEN_URL,
        client_id=get_oauth2_config().github_client_id,
        scope=GITHUB_SCOPE,
        redirect_uri=get_oauth2_config().github_redirect_uri,
    )
)

auth_client_registry.add(
    GithubAuthClient(
        auth_url=GITHUB_AUTH_URL,
        token_url=GITHUB_AUTH_URL,
        client_id=get_oauth2_config().github_client_id,
        client_secret=get_oauth2_config().github_client_secret,
        user_url=GITHUB_USER_URL,
    )
)


def mint_state_token(p: IdP = Query(...), u: str = Query("")):
    return StateToken.mint(idp=p, uistate=u)


def get_state_token_db() -> StateTokenDB:
    return state_token_db


def get_login_client(p: IdP = Query(...)) -> OAuth2LoginClient:
    return login_client_registry.get(p)


def get_auth_client(p: IdP = Query(...)) -> OAuth2AuthClient:
    return auth_client_registry.get(p)


def get_user_db() -> UserDB:
    return fake_user_db


@auth_router.get("/login")
async def auth_url_redirect(
    token: StateToken = Depends(mint_state_token),
    login_client: OAuth2LoginClient = Depends(get_login_client),
    state_token_db: StateTokenDB = Depends(get_state_token_db),
):
    try:
        auth_url = login_client.create_auth_url()
        state_token_db.store(token)
    except Exception as ex:
        print(ex)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Request",
        )

    return RedirectResponse(auth_url)


@auth_router.get("/auth/github", response_model=AccessRefreshToken)
async def auth_callback(
    request: Request,
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    state_token_db: StateTokenDB = Depends(get_state_token_db),
    user_db: UserDB = Depends(get_user_db),
):
    auth_error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Authorization Failed",
    )

    # should not contain more then 2 params in callback
    if not code or not state or len(request.query_params) > 2:
        raise auth_error

    # verify that we have issued the token and pop it
    token = state_token_db.pop_and_verify(state)
    if not token:
        raise auth_error

    auth_client = get_auth_client(token.provider)
    try:
        (grant, user_dict) = await auth_client.authorize(code=code, state=token.state)
        # ask for email if not present
        # send a confirmation email
        # verify the email
        # activate the account
        email = auth_client.get_email_str(user_dict)
        provider_id = auth_client.get_provider_id(user_dict)
        user = user_db.get(provider_id)
        # github username: user_dict["login"]
        # can be changed after the account creation

        if user is None:
            user = {}
            user["uuid"] = str(uuid4())
            user["scope"] = "episense:demo"
            provider = auth_client.idp.value
            user["provider"] = provider
            user_db.store(provider_id, provider, user)
            user = user_db.get(provider_id, provider)
        debug(user)

        # issue toke claims
        token_claims = TokenClaims(sub=user["uuid"], scopes=user["scopes"])
        token = token_claims.mint_access_refresh_token()
        debug(token)
        return token

    except Exception as ex:
        import traceback

        traceback.print_exc(ex)
        raise auth_error
