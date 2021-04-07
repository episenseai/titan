from fastapi import FastAPI

from .exceptions.passwd import passwd_exception_handlers
from .router.internal import admins_router_internal, apis_router_internal, users_router_internal
from .router.public import admins_router, apis_router, users_router
from .settings.backends import TEST_DATABSE, check_table_existence, initialize_JWKS_keys, state_tokens_db

all_exception_handlers = {}
all_exception_handlers.update(passwd_exception_handlers)

app = FastAPI(exception_handlers=all_exception_handlers)  # noqa


@app.on_event("startup")
async def startup():
    await TEST_DATABSE.connect()
    await check_table_existence()
    await state_tokens_db.connect()
    # Run in production
    # await initialize_JWKS_keys()


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
