from typing import Optional
from uuid import uuid4

import httpx
from devtools import debug
from fastapi import APIRouter, Query, Request, status, Depends
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse

from ..tokens.jwt import AccessRefreshToken, TokenClaims
from .state import StateTokenDB, StateToken
from .idp import IdP, OAuth2LoginClient, Oauth2ClientRegistry
from .github import GithubLoginClient
from .google import GoogleLoginClient
from ..settings import get_oauth2_config
from ..accounts.user import UserDB

auth_router = APIRouter()
user_db = UserDB()
state_token_db = StateTokenDB()
login_client_registry = Oauth2ClientRegistry(OAuth2LoginClient)

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


def mint_state_token(p: IdP = Query(...), u: str = Query("")):
    return StateToken.mint(provider=p, uistate=u)


def get_state_token_db() -> StateTokenDB:
    return state_token_db


def oauth2_login_client(p: IdP = Query(...)) -> OAuth2LoginClient:
    return login_client_registry.get(p)


@auth_router.get("/login")
async def auth_url_redirect(
    token: StateToken = Depends(mint_state_token),
    login_client: OAuth2LoginClient = Depends(oauth2_login_client),
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
async def auth_callback(request: Request, code: Optional[str] = Query(None), state: Optional[str] = Query(None)):
    auth_error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Authorization Failed",
    )

    # should not contain more then 2 params in callback
    if not code or not state or len(request.query_params) > 2:
        raise auth_error

    # if not state_token_db.verified(state):
    # raise auth_error
    try:
        url_params = AccessTokenURLParams(
            client_id=GITHUB_CLIENT_ID, client_secret=GITHUB_CLIENT_SECRET, code=code, state=state
        )
        debug(url_params)
        async with httpx.AsyncClient() as client:
            token_response = await client.post(GITHUB_TOKEN_URL, params=url_params.dict())
            decoded_form = token_response.content.decode()
            debug(token_response, token_response.status_code, decoded_form)

            # check X-rate-limit error

            response_dict = dict(parse_qsl(decoded_form))
            debug(response_dict)
            github_access_token = response_dict.get("access_token", None)
            github_ttype = response_dict.get("token_type", None)
            if github_access_token is None:
                raise ValueError("Can not get access token from github")
            if github_ttype.lower() != "bearer":
                raise ValueError("token_type error from github")
            github_header = {"Authorization": f"token {github_access_token}"}
            debug(github_access_token, github_header)

            user_response = await client.get(GITHUB_USER_URL, headers=github_header)
            debug(user_response.headers, user_response.text, user_response.encoding)
            github_user = user_response.json()
            debug(github_user)

        user = user_db.get(github_user["login"])
        if user is None:
            github_user["uuid"] = str(uuid4())
            github_user["scopes"] = "episense:demo"
            user_db.store(github_user["login"], github_user)
            user = user_db.get(github_user["login"])
        debug(user)
        # email might not be prsent if the user has marked it as private
        # maybe redirect here to owr own url to get other user info and then
        # issue tokens

        token_claims = TokenClaims(sub=user["uuid"], scopes=user["scopes"])
        token = token_claims.mint_access_refresh_token()
        debug(token)
        return token
    except Exception as ex:
        import traceback

        traceback.print_exc()
        print(ex)
        raise auth_error
