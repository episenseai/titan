from devtools import debug
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordRequestForm

from ..jwt import TokenClaims, XAccessToken, validate_get_decoded_token
from ..settings.backends import admins_db, users_db

admin_router = APIRouter(prefix="/x", tags=["x"])

auth_bearer = HTTPBearer()


@admin_router.post("/token", response_model=XAccessToken, response_model_exclude_none=True)
async def get_access_token(
    authorization: HTTPAuthorizationCredentials = Security(auth_bearer),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Validate Bearer token
    decoded_token = await validate_get_decoded_token(authorization.credentials)
    # decoded_token be an access_token not refresh_token/xaccess_token
    if decoded_token is None or decoded_token.get("ttype", None) != "access_token":
        raise auth_error

    # Check if the user is in 'users' database
    user = await users_db.get(userid=decoded_token["sub"])
    if user is None:
        raise auth_error

    # Check if the the user is in 'admins' database
    admin = await admins_db.get_admin(email=user.email, username=form_data.username)
    if admin is None:
        raise auth_error

    # admin is fisabled by superadmin
    if admin.frozen:
        raise auth_error

    # Verify password
    is_verified = await admins_db.verify_password(admin=admin, password=form_data.password)
    if not is_verified:
        raise auth_error

    # Mint Token
    token_claims = TokenClaims(sub=str(admin.adminid), scope=admin.scope)
    xaccess_token = token_claims.mint_xaccess_token()

    return xaccess_token
