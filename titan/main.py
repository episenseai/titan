from fastapi import FastAPI


from .exceptions.passwd import passwd_exception_handlers
from .router.internal import admins_router_internal, apis_router_internal, users_router_internal
from .router.public import admins_router, apis_router, users_router
from .settings.backends import postgres_database, check_table_existence, initialize_JWKS_keys

all_exception_handlers = {}
all_exception_handlers.update(passwd_exception_handlers)

app = FastAPI(exception_handlers=all_exception_handlers)  # noqa


@app.on_event("startup")
async def startup():
    for x in range(3):
        try:
            await postgres_database.connect()
            break
        except ConnectionRefusedError as ex:
            if x != 2:
                print("Will try connecting to postgres in a few seconds")
                import time

                time.sleep(5)
                continue
            print(f"Tried 3 times to connect to postgres database but failed: \n {ex}")
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
