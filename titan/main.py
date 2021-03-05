from fastapi import FastAPI
from .exception_handlers.passwd import passwd_exception_handlers
from .public.oauth2 import auth_router

all_exception_handlers = {}
all_exception_handlers.update(passwd_exception_handlers)

app = FastAPI(exception_handlers=all_exception_handlers)  # noqa
app.include_router(auth_router)
