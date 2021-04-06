from fastapi import FastAPI

from .exceptions.passwd import passwd_exception_handlers
from .router.public import admins_router, apis_router, users_router
from .router.internal import users_router_internal, admins_router_internal, apis_router_internal
from .settings.backends import (
    admins_db,
    apis_db,
    state_tokens_db,
    users_db,
    admins_db_internal,
    users_db_internal,
    apis_db_internal,
)
from .settings.idp import google_auth_client

all_exception_handlers = {}
all_exception_handlers.update(passwd_exception_handlers)

app = FastAPI(exception_handlers=all_exception_handlers)  # noqa


@app.on_event("startup")
async def startup():
    await users_db.connect()
    await apis_db.connect()
    await admins_db.connect()
    await users_db_internal.connect()
    await apis_db_internal.connect()
    await admins_db_internal.connect()
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
    await users_db.disconnect()
    await apis_db.disconnect()
    await admins_db.disconnect()
    await users_db_internal.disconnect()
    await apis_db_internal.disconnect()
    await admins_db_internal.disconnect()
    await state_tokens_db.disconnect()


app.include_router(users_router)
app.include_router(admins_router)
app.include_router(apis_router)
app.include_router(users_router_internal)
app.include_router(admins_router_internal)
app.include_router(apis_router_internal)
