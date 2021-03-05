from typing import Optional

from fastapi import APIRouter, Depends, Form, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from ..accounts.user import autheticate_user
from ..tokens.jwt import AccessRefreshToken, AccessToken, TokenClaims

tokens_router = APIRouter()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@tokens_router.post(
    "/token",
    response_model=AccessRefreshToken,
    response_model_include={"access_token", "token_type", "refresh_token"},
)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await autheticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password in the request",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        token_claims = TokenClaims(sub=user.username)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="TODO",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = token_claims.mint_access_refresh_token()
    return token


class OAuth2RefreshTokenRequestForm:
    def __init__(
        self,
        grant_type: str = Form(None, regex="refresh_token"),
        refresh_token: str = Form(...),
        client_id: Optional[str] = Form(None),
        client_secret: Optional[str] = Form(None),
    ):
        self.grant_type = grant_type
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret


def is_valid_token() -> bool:
    pass


def is_refresh_token() -> bool:
    pass


def is_access_token() -> bool:
    pass


def is_access_token_revoked() -> bool:
    False


def is_refresh_token_revoked() -> bool:
    False


"""
@tokens_router.post(
    "/refresh",
    response_class=AccessToken,
    response_model_include={"access_token", "token_type"},
)
async def refresh(form_data: OAuth2RefreshTokenRequestForm = Depends()):
    pass
"""
