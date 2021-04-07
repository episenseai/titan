from typing import Optional

from fastapi import APIRouter, Query, Request, status
from fastapi.exceptions import HTTPException
from fastapi.responses import RedirectResponse

from ...auth.models import IdentityProvider
from ...auth.state import StateToken
from ...exceptions.exc import Oauth2AuthError, OAuth2EmailPrivdedError
from ...logger import logger
from ...settings.backends import state_tokens_db, users_db
from ...settings.idp import github_auth_client, github_login_client, google_auth_client, google_login_client
from ...tokens import TokenClaims
from ...utils import ImmutBaseModel

users_router = APIRouter(tags=["user/token"])


@users_router.get("/login")
async def auth_redirect_url(
    p: IdentityProvider = Query(...),
    ustate: str = Query(""),
):
    if p == IdentityProvider.github:
        login_client = github_login_client
    elif p == IdentityProvider.google:
        login_client = google_login_client
    else:
        logger.error(f"Can't issue state token: (idp={p})")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    # include nonce if required
    if p == IdentityProvider.google:
        with_nonce = True
    else:
        with_nonce = False

    state_token = StateToken.issue(idp=p, ustate=ustate, with_nonce=with_nonce)
    logger.info(f"Issued state token: (idp={p})")

    auth_callback_url = login_client.create_auth_url(state_token)
    state_tokens_db.store(state_token)
    return RedirectResponse(auth_callback_url)


class Token(ImmutBaseModel):
    access_token: str
    expires_in: int
    refresh_token: Optional[str] = None
    full_name: Optional[str] = None
    picture: Optional[str] = None
    ustate: Optional[str] = None


# Authorization callback URL
@users_router.get("/auth", response_model=Token, response_model_exclude_none=True)
async def get_access_token(
    request: Request,
    error: Optional[str] = Query(None),
    code: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    scope: Optional[str] = Query(None),
):
    authentication_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed",
    )

    if error is not None:
        logger.info(f"Auth callback error: ({error=}, {request.query_params=})")
        raise authentication_error
    if code is None:
        logger.info(f"Auth callback error: missing 'code' ({request.query_params=})")
        raise authentication_error
    # Ideally, this should not happen if `code` is present in callback.
    if state is None:
        logger.info(f"Auth callback error: missing 'state' ({request.query_params=})")
        raise authentication_error

    state_token = state_tokens_db.pop_and_verify(state)
    if not state_token:
        logger.info(f"Suspcious user login attempt: state_token not issued 'state' ({request.query_params=})")
        raise authentication_error

    if state_token.idp == IdentityProvider.github:
        auth_client = github_auth_client
    elif state_token.idp == IdentityProvider.google:
        auth_client = google_auth_client
    else:
        # This should not happen.
        logger.error(f"Unexpected: ({state_token.idp}) not recognized")
        raise authentication_error

    try:
        auth_user = await auth_client.authorize(code=code, token=state_token)
        logger.info(f"Oauth successfull: (idp={state_token.idp}, email={auth_user.email})")
    except OAuth2EmailPrivdedError as exc:
        logger.exception(f"Oauth failed: (idp={state_token.idp}) {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: primary email is not verified with provider.",
        )
    except Oauth2AuthError as exc:
        logger.error("Oauth failed: (idp={state_token.idp}) {exc}")
        raise authentication_error

    user = await users_db.get_by_email(email=auth_user.email)

    if user is None:
        logger.info("New user: (idp={state_token.idp}, email={auth_user.email})")
        # scope assgined to the user when he first signs up
        SIGNUP_SCOPE = "basic"
        # we are not doing out own email verification for now.
        SIGNUP_EMAIL_VERIFIED = False
        # create a new user
        new_user = await users_db.create(
            email=auth_user.email,
            idp=auth_user.idp.value,
            idp_userid=auth_user.idp_userid,
            idp_username=auth_user.idp_username,
            full_name=auth_user.full_name,
            picture=auth_user.picture,
            scope=SIGNUP_SCOPE,
            email_verified=SIGNUP_EMAIL_VERIFIED,
        )

        if new_user is None:
            logger.error(f"Create new user: (idp={state_token.idp}, email={auth_user.email})")
            raise authentication_error
        logger.info(f"Created new user: (idp={state_token.idp}, user={new_user.userid}, scope={SIGNUP_SCOPE})")
        user = new_user
    else:
        if user.idp != state_token.idp:
            logger.info(f"Account exists error: (idp={state_token.idp}, account_idp={user.idp}, user={user.userid}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account already exists with a different login provider",
            )

        if user.frozen:
            logger.info(f"User forzen: (user={user.userid})")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account frozen",
            )

        # update user info
        await users_db.update(
            user=user,
            idp_username=auth_user.idp_username,
            full_name=auth_user.full_name,
            picture=auth_user.picture,
        )

    # Do we need to manually approve the account before activation????

    # TODO: Invalidate previous tokens for users when issuing a new one
    claims = TokenClaims(sub=user.userid, scope=user.scope)
    issued_token = claims.issue_access_token()
    token = Token(
        full_name=auth_user.full_name,
        picture=auth_user.picture,
        ustate=state_token.ustate,
        **issued_token.dict(),
    )
    logger.info(f"Issued access_token: (user={claims.sub}, idp={state_token.idp})")
    return token
