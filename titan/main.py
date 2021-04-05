from fastapi import FastAPI

from .exceptions.passwd import passwd_exception_handlers
from .routes.public import admins_router, apis_router, users_router
from .settings.backends import admins_db, apis_db, state_tokens_db, users_db

all_exception_handlers = {}
all_exception_handlers.update(passwd_exception_handlers)

app = FastAPI(exception_handlers=all_exception_handlers)  # noqa


@app.on_event("startup")
async def startup():
    await users_db.connect()
    await apis_db.connect()
    await admins_db.connect()
    await state_tokens_db.connect()


@app.on_event("shutdown")
async def shutdown():
    await users_db.disconnect()
    await apis_db.disconnect()
    await admins_db.disconnect()
    await state_tokens_db.disconnect()


app.include_router(users_router)
app.include_router(admins_router)
app.include_router(apis_router)
