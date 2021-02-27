from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, SecurityScopes
from passlib.context import CryptContext
from pydantic import BaseModel
from pydantic.types import UUID4, EmailStr

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    },
    "alice": {
        "username": "alice",
        "full_name": "Alice Chains",
        "email": "alicechains@example.com",
        "hashed_password": "$2b$12$gSvqqUPvlXP2tfVFaWK1Be7DlH.PKZbv5H8KnzzVgXXbVxpva.pFm",
        "disabled": True,
    },
}

# ["auto"] will configure the CryptContext instance to deprecate all
# supported schemes except for the default scheme.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", truncate_error=True)


def get_password_hash(password: str):
    return pwd_context.hash(password)


def hash_verify_and_update(plain_password: str, hashed_password: str):
    return pwd_context.verify_and_update(plain_password, hashed_password)


def update_password_hash(username: str, new_hashed_password: str):
    pass


def verify_password(username: str, plain_password: str, hashed_password: str) -> bool:
    valid_password, new_hashed_password = hash_verify_and_update(plain_password, hashed_password)
    if valid_password:
        if new_hashed_password:
            update_password_hash(username, new_hashed_password)
    return valid_password


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
