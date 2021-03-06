from typing import Optional
from uuid import uuid4

from devtools import debug
from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse

from ..accounts.user import UserDB
from ..oauth2.github import GithubAuthClient, GithubLoginClient
from ..oauth2.google import GoogleAuthClient, GoogleLoginClient
from ..oauth2.models import IdP, OAuth2AuthClient, OAuth2LoginClient
from ..oauth2.state import StateToken, StateTokenDB
from ..settings import get_oauth2_settings
from ..tokens.jwt import AccessRefreshToken, TokenClaims

auth_router = APIRouter()
fake_user_db = UserDB()
fake_state_token_db = StateTokenDB()

github_login_client = GithubLoginClient.new(
    client_id=get_oauth2_settings().github_client_id,
    scope=get_oauth2_settings().github_client_scope,
    redirect_uri=get_oauth2_settings().github_redirect_uri,
)

github_auth_client = GithubAuthClient.new(
    client_id=get_oauth2_settings().github_client_id,
    scope=get_oauth2_settings().github_client_scope,
    redirect_uri=get_oauth2_settings().github_redirect_uri,
    client_secret=get_oauth2_settings().github_client_secret,
)

google_login_client = GoogleLoginClient.new(
    client_id=get_oauth2_settings().google_client_id,
    scope=get_oauth2_settings().google_client_scope,
    redirect_uri=get_oauth2_settings().google_redirect_uri,
    iss=get_oauth2_settings().google_client_iss,
)

google_auth_client = GoogleAuthClient.new(
    client_id=get_oauth2_settings().google_client_id,
    scope=get_oauth2_settings().google_client_scope,
    redirect_uri=get_oauth2_settings().google_redirect_uri,
    client_secret=get_oauth2_settings().google_client_secret,
    iss=get_oauth2_settings().google_client_iss,
)


def mint_state_token(p: IdP = Query(...), u: str = Query("")):
    if p == IdP.google:
        with_nonce = True
    else:
        with_nonce = False
    return StateToken.mint(idp=p, uistate=u, with_nonce=with_nonce)


def get_state_token_db() -> StateTokenDB:
    return fake_state_token_db


def get_login_client(p: IdP = Query(...)) -> OAuth2LoginClient:
    if p == IdP.github:
        return github_login_client
    elif p == IdP.google:
        return google_login_client
    else:
        raise NotImplementedError()


def get_auth_client(p: IdP = Query(...)) -> OAuth2AuthClient:
    if p == IdP.github:
        return github_auth_client
    if p == IdP.google:
        return google_auth_client
    else:
        raise NotImplementedError()


def get_user_db() -> UserDB:
    return fake_user_db


@auth_router.get("/login")
async def auth_url_redirect(
    token: StateToken = Depends(mint_state_token),
    login_client: OAuth2LoginClient = Depends(get_login_client),
    state_token_db: StateTokenDB = Depends(get_state_token_db),
):
    try:
        from devtools import debug

        debug(token, login_client, state_token_db)
        auth_url = login_client.create_auth_url(token)
        state_token_db.store(token)
    except Exception as ex:
        import traceback

        traceback.print_exc(ex)
        print(ex)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Request",
        )

    return RedirectResponse(auth_url)


@auth_router.get("/auth", response_model=AccessRefreshToken)
async def auth_callback(
    request: Request,
    error: Optional[str] = Query(None),
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
    state_token_db: StateTokenDB = Depends(get_state_token_db),
    user_db: UserDB = Depends(get_user_db),
):
    auth_error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Authorization Failed",
    )

    if error is not None:
        print("{error=} returned from auth callback")
        raise auth_error
    if code is None:
        print("'code' param could not be found in the request")
        raise auth_error
    if state is None:
        print("'state' param could not be found in the request")
        raise auth_error

    debug(code, state, scope, request.query_params)

    # verify that we have issued the token and pop it
    token = state_token_db.pop_and_verify(state)
    if not token:
        raise auth_error

    auth_client = get_auth_client(token.idp)

    (grant, user_dict) = await auth_client.authorize(code=code, token=token)
    # ask for email if not present
    # send a confirmation email
    # verify the email
    # activate the account
    email = auth_client.get_email_str(user_dict)
    idp = auth_client.idp.value
    provider_id = auth_client.get_provider_id(user_dict)
    user = user_db.get(provider_id, idp)
    # github username: user_dict["login"]
    # can be changed after the account creation

    if user is None:
        user = {}
        user["uuid"] = str(uuid4())
        # assign default scope to the new account
        user["scope"] = "episense:demo"
        user["provider"] = idp
        user_db.store(provider_id, idp, user)
        user = user_db.get(provider_id, idp)
    debug(user)

    # issue toke claims
    token_claims = TokenClaims(sub=user["uuid"], scopes=user["scope"])
    access_token = token_claims.mint_access_refresh_token()
    debug(access_token)
    return access_token
