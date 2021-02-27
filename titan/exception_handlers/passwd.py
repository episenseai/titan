from fastapi import status
from fastapi.responses import ORJSONResponse
from fastapi.encoders import jsonable_encoder
from passlib.exc import PasswordValueError, PasswordSizeError, PasswordTruncateError


async def bcrypt_password_error(request, exc):
    return ORJSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder({"detail": "choose a shorter password"})
    )


async def password_size_error(request, exc):
    return ORJSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder({"detail": "choose a shorter password"})
    )


async def password_value_error(request, exc):
    return ORJSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder({"detail": "malformed request"})
    )


passwd_exception_handlers = {
    PasswordTruncateError: bcrypt_password_error,
    PasswordSizeError: password_size_error,
    PasswordValueError: password_value_error,
}
