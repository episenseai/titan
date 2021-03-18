from fastapi import FastAPI

from .exception_handlers.passwd import passwd_exception_handlers
from .public.oauth2 import auth_router
from .public.admin import admin_router
from .userdb import user_db
from .admindb import admin_db

all_exception_handlers = {}
all_exception_handlers.update(passwd_exception_handlers)

app = FastAPI(exception_handlers=all_exception_handlers)  # noqa


@app.on_event("startup")
async def startup():
    await user_db.connect()
    await admin_db.connect()


@app.on_event("shutdown")
async def shutdown():
    await user_db.disconnect()
    await admin_db.disconnect()


app.include_router(auth_router)
app.include_router(admin_router)
