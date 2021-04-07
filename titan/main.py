from fastapi import FastAPI

from .exceptions.passwd import passwd_exception_handlers
from .router.internal import admins_router_internal, apis_router_internal, users_router_internal
from .router.public import admins_router, apis_router, users_router
from .settings.backends import TEST_DATABSE, check_table_existence, state_tokens_db
from .settings.idp import google_auth_client

all_exception_handlers = {}
all_exception_handlers.update(passwd_exception_handlers)

app = FastAPI(exception_handlers=all_exception_handlers)  # noqa


@app.on_event("startup")
async def startup():
    await TEST_DATABSE.connect()
    await check_table_existence()
    await state_tokens_db.connect()
    # run this in production to aovid fetching keys over and over again
    """
    if google_auth_client.jwks_uri is None:
        raise RuntimeError("Google missing JWKS uri: needed for GoogleAuthClient")
    try:
        await google_auth_client.update_jwks_keys()
    except Exception:
        raise RuntimeError("Could not download JWKS keys from Google")
    """


@app.on_event("shutdown")
async def shutdown():
    await TEST_DATABSE.disconnect()
    await state_tokens_db.disconnect()


app.include_router(users_router)
app.include_router(admins_router)
app.include_router(apis_router)
app.include_router(users_router_internal)
app.include_router(admins_router_internal)
app.include_router(apis_router_internal)
