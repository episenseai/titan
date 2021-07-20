from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .exceptions.passwd import passwd_exception_handlers
from .logger import logger
from .router.internal import admins_router_internal, apis_router_internal, users_router_internal
from .router.public import admins_router, apis_router, users_router
from .settings.backends import (
    check_table_existence,
    initialize_JWKS_keys,
    postgres_connect,
    postgres_database,
)
from .settings.env import env

all_exception_handlers = {}
all_exception_handlers.update(passwd_exception_handlers)

app = FastAPI(exception_handlers=all_exception_handlers)  # noqa

origins = [
    "http://localhost",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    if not await postgres_connect():
        exit(1)
    if not await check_table_existence():
        exit(1)

    # Run in production
    # await initialize_JWKS_keys()


@app.on_event("shutdown")
async def shutdown():
    await postgres_database.disconnect()


app.include_router(users_router)
app.include_router(admins_router)
app.include_router(apis_router)
app.include_router(users_router_internal)
app.include_router(admins_router_internal)
app.include_router(apis_router_internal)
