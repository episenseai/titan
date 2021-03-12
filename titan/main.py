from fastapi import FastAPI
from .exception_handlers.passwd import passwd_exception_handlers
from .public.oauth2 import auth_router
from .accounts.user import database

all_exception_handlers = {}
all_exception_handlers.update(passwd_exception_handlers)

app = FastAPI(exception_handlers=all_exception_handlers)  # noqa


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


app.include_router(auth_router)
