from typing import Optional
from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from pydantic.types import UUID4, EmailStr
from datetime import datetime

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class UserID(BaseModel):
    uuid: UUID4


class User(UserID):
    username: EmailStr
    full_name: str
    hashed_pass: str
    disabled: bool = False
    email_verified: bool = False
    scopes: Optional[str] = None
    created_at: datetime


@app.post("/token")
async def login_for_access_token():
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
