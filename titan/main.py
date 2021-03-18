from fastapi import FastAPI

from .admindb import admin_db
from .exception_handlers.passwd import passwd_exception_handlers
from .public.admin import admin_router
from .public.oauth2 import auth_router
from .statetokendb import state_token_db
from .userdb import user_db

all_exception_handlers = {}
all_exception_handlers.update(passwd_exception_handlers)

app = FastAPI(exception_handlers=all_exception_handlers)  # noqa


@app.on_event("startup")
async def startup():
    await user_db.connect()
    await admin_db.connect()
    await state_token_db.connect()


@app.on_event("shutdown")
async def shutdown():
    await user_db.disconnect()
    await admin_db.disconnect()
    await state_token_db.disconnect()


app.include_router(auth_router)
app.include_router(admin_router)
