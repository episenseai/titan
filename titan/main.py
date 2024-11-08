import asyncio

from fastapi import FastAPI
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

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
from .settings.env import Env, env

# Install global exception handlers for the exceptions we care about
all_exception_handlers = {}
all_exception_handlers.update(passwd_exception_handlers)


# https://fastapi.tiangolo.com/tutorial/metadata/
disable_api_description = True

if env().ENV == Env.PRODUCTION or disable_api_description:
    app = FastAPI(
        exception_handlers=all_exception_handlers, openapi_url=None, docs_url=None, redoc_url=None
    )
else:
    app = FastAPI(exception_handlers=all_exception_handlers)


if env().ENV == Env.PRODUCTION:

    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(request, exc):
        """
        HTTPException tarpit
        --------------------

        Introduce a delay in response when an HTTException is created, more so when
        the exception is of 401/403 type.

        NOTE: Ideally this should not be inside the application. It should be done by
        running our own ingress proxy application for handling this logic.
        """
        if exc.status_code == 401 or exc.status_code == 403:
            await asyncio.sleep(5)
        else:
            await asyncio.sleep(2)
        return await http_exception_handler(request, exc)


if env().ENV == Env.PRODUCTION:

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        """
        RequestValidationError tarpit
        -----------------------------

        Introduce a delay in response the invalid data is supplied by the user and
        a pydantic validation error is raised.
        """
        await asyncio.sleep(2)
        return await request_validation_exception_handler(request, exc)


# This runs when the application starts
@app.on_event("startup")
async def startup():
    logger.warning(f"========== RUNNING IN [{env().ENV}] MODE ==========")
    if not await postgres_connect():
        exit(1)
    if not await check_table_existence():
        exit(1)
    # Constant reloading in dev mode will unnecessarily fetch keys over and over
    # again: in production we need to fail early if the keys could not be fetched.
    if env().ENV == Env.PRODUCTION:
        if not await initialize_JWKS_keys():
            exit(1)


# This runs when the application is winding down
@app.on_event("shutdown")
async def shutdown():
    await postgres_database.disconnect()


# Include routers for handling path requests
app.include_router(users_router)
app.include_router(admins_router)
app.include_router(apis_router)
app.include_router(users_router_internal)
app.include_router(admins_router_internal)
app.include_router(apis_router_internal)


# CORS middleware for handling Cross-Origin requests. If the frontend is running
# at a different origin than this application add that origin to the list.
#
# It's also possible to declare the list as "*" (a "wildcard") to say that all
# are allowed. But that will only allow certain types of communication,
# excluding everything that involves credentials: Cookies, Authorization headers
# like those used with Bearer Tokens, etc. So, for everything to work correctly,
# it's better to specify explicitly the allowed origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[env().CORS_ORIGIN] if env().CORS_ENABLED else [],
    allow_credentials=True,
    allow_methods=["*"] if env().CORS_ENABLED else [],
    allow_headers=["*"] if env().CORS_ENABLED else [],
)
