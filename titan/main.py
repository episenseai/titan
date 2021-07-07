from asyncpg.exceptions import (
    CannotConnectNowError,
    ClientCannotConnectError,
    ConnectionDoesNotExistError,
    ConnectionFailureError,
    ConnectionRejectionError,
)
from fastapi import FastAPI

from .exceptions.passwd import passwd_exception_handlers
from .logger import logger
from .router.internal import admins_router_internal, apis_router_internal, users_router_internal
from .router.public import admins_router, apis_router, users_router
from .settings.backends import check_table_existence, initialize_JWKS_keys, postgres_database
from .settings.env import env

all_exception_handlers = {}
all_exception_handlers.update(passwd_exception_handlers)

app = FastAPI(exception_handlers=all_exception_handlers)  # noqa


@app.on_event("startup")
async def startup():
    # seconds
    backoff_time = 5
    for x in range(4):
        try:
            await postgres_database.connect()
            break
        except (
            ConnectionRefusedError,
            CannotConnectNowError,
            ClientCannotConnectError,
            ConnectionDoesNotExistError,
            ConnectionFailureError,
            ConnectionRejectionError,
        ) as ex:
            if x != 3:
                logger.warn(f"Could not connect to {env().postgres_url}")
                logger.info(f"Retry connecting in {backoff_time}sec {env().postgres_url}")
                import time

                time.sleep(backoff_time)
                # linear backoff
                backoff_time = backoff_time + 3
                continue
            logger.exception(f"Tried 3 times to connect to postgres database but failed: \n {ex}")
            exit(1)
    await check_table_existence()
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
