from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ...logger import logger
from ...settings.backends import admins_db, users_db
from ...tokens import DecodedToken, TokenClaims
from ...utils import ImmutBaseModel
from ..depends import get_decoded_token, store_decoded_token, validate_ttype_access

admins_router = APIRouter(
    prefix="/x",
    tags=["admin/token"],
    dependencies=[
        Depends(store_decoded_token),
        # Can only get xaccess_token if one is holding an access_token
        Depends(validate_ttype_access),
    ],
)


class Token(ImmutBaseModel):
    access_token: str
    expires_in: int
    token_type: str


@admins_router.post("/token", response_model=Token, response_model_exclude_none=True)
async def get_xaccess_token(
    decoded_token: DecodedToken = Depends(get_decoded_token),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    authentication_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    frozen_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Account frozen",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = await users_db.get(userid=decoded_token.sub)

    # This should not happen as the token was issued for the user.
    if user is None:
        logger.error(f"Unexpected token: (user={decoded_token.sub}) not in users database ")
        raise authentication_error

    if user.frozen:
        logger.info(f"User frozen: can't issue admin token for (user={user.userid})")
        raise frozen_error

    admin = await admins_db.get_admin(email=user.email, username=form_data.username)

    if admin is None:
        logger.info(
            f"Failed admin login attempt: (username={form_data.username}, user={user.userid})"
        )
        raise credentials_error

    if admin.frozen:
        logger.info(
            f"Admin frozen: can't issue admin token for (user={user.userid}, admin={admin.adminid})"
        )
        raise frozen_error

    is_verified = await admins_db.verify_password(
        password=form_data.password, password_hash=admin.password
    )

    if not is_verified:
        logger.info(
            f"Failed admin login attempt: password verification (username={form_data.username}, user={user.userid})"
        )
        raise credentials_error

    # TODO: Invalidate previous xaccess_token for users when issuing a new one
    claims = TokenClaims(sub=user.userid, scope=admin.scope)
    issued_token = claims.issue_xaccess_token()
    logger.info(f"Issued xaccess_token: (user={user.userid}, admin={admin.adminid})")
    return issued_token
