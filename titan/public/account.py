from fastapi import APIRouter

user_rooter = APIRouter()


@user_rooter.post("/token")
async def login():
    pass


@user_rooter.post("/user")
async def new_user_account():
    pass


@user_rooter.get("/users/{uuid}")
async def user_info():
    pass


@user_rooter.get("/account_verification/email/{unique_id}")
async def account_verification_by_email():
    pass


@user_rooter.post("/forgot_password/new")
async def forgot_password_new():
    pass


@user_rooter.post("/password_resets/{unique_id}")
async def password_resets():
    # link expiry time
    pass
