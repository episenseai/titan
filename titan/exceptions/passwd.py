from traceback import print_exc

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import ORJSONResponse
from passlib.exc import PasswordSizeError, PasswordTruncateError, PasswordValueError

from .exc import Oauth2AuthError


async def bcrypt_password_error(request, exc):
    return ORJSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"detail": "choose a shorter password"}),
    )


async def password_size_error(request, exc):
    return ORJSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"detail": "choose a shorter password"}),
    )


async def password_value_error(request, exc):
    return ORJSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder({"detail": "malformed request"}),
    )


async def oauth2_authorization_error(request, exc):
    print_exc(exc)
    return ORJSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder({"detail": "auth error"})
    )


passwd_exception_handlers = {
    PasswordTruncateError: bcrypt_password_error,
    PasswordSizeError: password_size_error,
    PasswordValueError: password_value_error,
    Oauth2AuthError: oauth2_authorization_error,
}
