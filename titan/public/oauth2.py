from typing import Optional

from devtools import debug
from fastapi import APIRouter, Query, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse

from ..client import github_auth_client, github_login_client, google_auth_client, google_login_client
from ..exceptions import OAuth2EmailPrivdedError, OAuth2MissingInfo, OAuth2MissingScope
from ..oauth2.models import IdP
from ..oauth2.state import StateToken
from ..statedb import state_token_db
from ..tokens.jwt import AccessToken, TokenClaims
from ..userdb import user_db

auth_router = APIRouter()


@auth_router.get("/login")
async def auth_url_redirect(
    p: IdP = Query(...),
    u: Optional[str] = Query(None),
):
    auth_error = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid Request",
    )

    # determine identity provider
    if p == IdP.github:
        login_client = github_login_client
    elif p == IdP.google:
        login_client = google_login_client
    else:
        raise auth_error

    # include nonce if required
    if p == IdP.google:
        with_nonce = True
    else:
        with_nonce = False
    state_token = StateToken.mint(idp=p, uistate=u, with_nonce=with_nonce)

    debug(state_token, login_client, state_token_db)
    auth_url = login_client.create_auth_url(state_token)
    state_token_db.store(state_token)

    return RedirectResponse(auth_url)


@auth_router.get("/auth", response_model=AccessToken, response_model_exclude_none=True)
async def auth_callback(
    request: Request,
    error: Optional[str] = Query(None),
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
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

    # determine identity provider
    if token.idp == IdP.github:
        auth_client = github_auth_client
    elif token.idp == IdP.google:
        auth_client = google_auth_client
    else:
        raise auth_error

    try:
        auth_user = await auth_client.authorize(code=code, token=token)
        debug(auth_user)
    except (OAuth2MissingScope, OAuth2MissingInfo, OAuth2EmailPrivdedError) as exc:
        print(exc)
        raise auth_error

    user = await user_db.get_user(auth_user.email)
    debug(user)

    if user is None:
        await user_db.create_user(auth_user, disabled=False, email_verified=False)
        user = await user_db.get_user(auth_user.email)
        # unexpected: should never happen
        if user is None:
            raise auth_error
    else:
        # user has already signed up with the email using a different
        # identity provider.
        if user.idp != token.idp:
            raise auth_error
        # update user info
        await user_db.try_update_user(user=user)

    # send a confirmation email and verify the email (our own verification)
    # activate the account after manual approval
    token_claims = TokenClaims(sub=str(user.guid), scope=user.scope)
    access_token = token_claims.mint_access_refresh_token(user=user, token=token)
    debug(access_token)

    return access_token
