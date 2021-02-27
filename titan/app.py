from fastapi import FastAPI, status
from fastapi.responses import ORJSONResponse
from fastapi.encoders import jsonable_encoder
from passlib.exc import PasswordValueError, PasswordSizeError, PasswordTruncateError

app = FastAPI(default_response_class=ORJSONResponse)


@app.exception_handler(PasswordTruncateError)
async def bcrypt_password_error(request, exc):
    return ORJSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder({"detail": "choose a shorter password"})
    )


@app.exception_handler(PasswordSizeError)
async def password_size_error(request, exc):
    return ORJSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder({"detail": "choose a shorter password"})
    )


@app.exception_handler(PasswordValueError)
async def password_value_error(request, exc):
    return ORJSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content=jsonable_encoder({"detail": "malformed request"})
    )
