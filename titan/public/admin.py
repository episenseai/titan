from devtools import debug
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, OAuth2PasswordRequestForm

from ..admindb import admin_db
from ..tokens.jwt import TokenClaims, XAccessToken, validate_and_get_token_claims_dict
from ..userdb import user_db

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
    decoded_token = await validate_and_get_token_claims_dict(authorization.credentials)
    # decoded_token be an access_token not refresh_token/xaccess_token
    if decoded_token is None or decoded_token.get("ttype", None) != "access_token":
        raise auth_error

    # Check if the user is in 'users' database
    user = await user_db.get_user(userid=decoded_token["sub"])
    if user is None:
        raise auth_error

    # Check if the the user is in 'admins' database
    admin = await admin_db.get_admin(email=user.email, username=form_data.username)
    if admin is None:
        raise auth_error

    # Verify password
    is_verified = await admin_db.verify_password(admin=admin, password=form_data.password)
    if not is_verified:
        raise auth_error

    # Mint Token
    token_claims = TokenClaims(sub=str(admin.adminid), scope=admin.scope)
    xaccess_token = token_claims.mint_xaccess_token(admin=admin)

    return xaccess_token
