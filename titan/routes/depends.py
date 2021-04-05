from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from ..jwt import DecodedToken, validate_get_decoded_token
from ..logger import logger
from ..utils import StrictBaseModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


async def store_decoded_token(request: Request, token: str = Depends(oauth2_scheme)) -> None:
    """
    Store the `DecodedToken` into `request.state`
    """
    decoded_token = await validate_get_decoded_token(token)
    if decoded_token is None:
        error_msg = "Authentication Error: Invalid credentials"
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
    except AttributeError as exc:
        logger.critical("get_decoded_token should be called after store_decoded_token", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Error",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def validate_ttype_is_access(request: Request) -> None:
    """
    This should never return `None`. `store_decoded_token` should have been
    called before calling this function.
    """
    try:
        decoded_token: DecodedToken = request.state.decoded_token
        if decoded_token.ttype != "access_token":
            error_msg = "Authentication Error: Invalid credentials."
            logger.error(
                f"{error_msg} Needed 'access_token' but found '{decoded_token.ttype}' for user={decoded_token.sub}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_msg,
                headers={"WWW-Authenticate": "Bearer"},
            )
    except AttributeError as exc:
        logger.critical("validate_ttype_access should be called after store_decoded_token", exc_info=exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Error",
            headers={"WWW-Authenticate": "Bearer"},
        )


class EmptyBody(StrictBaseModel):
    pass


def empty_body(reuest_body: Optional[EmptyBody] = None):
    """
    Checks if the body is `empty` or `{}`, otherwise raises `ValidationError`
    """
    pass
