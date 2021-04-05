from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from ..logger import logger
from ..tokens import DecodedToken, validate_token, TokenType
from ..utils import StrictBaseModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


async def store_decoded_token(request: Request, token: str = Depends(oauth2_scheme)) -> None:
    """
    Store the `DecodedToken` into `request.state`
    """
    decoded_token = await validate_token(token)
    if decoded_token is None:
        error_msg = "Authentication Error"
        logger.error(f"{error_msg} TOKEN={token}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg,
            headers={"WWW-Authenticate": "Bearer"},
        )
    request.state.decoded_token = decoded_token


async def get_decoded_token(request: Request) -> DecodedToken:
    """
    This should never return `None`. `store_decoded_token` should have been
    called before calling this function.
    """
    try:
        return request.state.decoded_token
    except AttributeError:
        logger.error("get_decoded_token should be called after store_decoded_token", exc_info=1)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Error",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def validate_ttype(request: Request, ttype: TokenType) -> None:
    """
    This should never return `None`. `store_decoded_token` should have been
    called before calling this function.
    """
    try:
        decoded_token: DecodedToken = request.state.decoded_token
        if decoded_token.ttype != ttype:
            error_msg = "Not authenticated"
            logger.error(f"{error_msg}: ({ttype=}, {decoded_token.ttype=}, user={decoded_token.sub})")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_msg,
                headers={"WWW-Authenticate": "Bearer"},
            )
    except AttributeError:
        logger.error("validate_ttype should be called after store_decoded_token", exc_info=1)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def validate_ttype_access(request: Request) -> None:
    return await validate_ttype(request, ttype=TokenType.ACCESS_TOKEN)


async def validate_ttype_xaccess(request: Request) -> None:
    return await validate_ttype(request, ttype=TokenType.XACCESS_TOKEN)


class EmptyBody(StrictBaseModel):
    pass


def empty_body(reuest_body: Optional[EmptyBody] = None):
    """
    Checks if the body is `empty` or `{}`, otherwise raises `ValidationError`
    """
    pass
