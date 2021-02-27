from fastapi import FastAPI

app = FastAPI()


@app.post("/token")
async def login():
    pass


@app.post("/user")
async def new_user_account():
    pass


@app.get("/users/{uuid}")
async def user_info():
    pass


@app.get("/account_verification/email/{unique_id}")
async def account_verification_by_email():
    pass


@app.post("/forgot_password/new")
async def forgot_password_new():
    pass


@app.post("/password_resets/{unique_id}")
async def password_resets():
    # link expiry time
    pass
