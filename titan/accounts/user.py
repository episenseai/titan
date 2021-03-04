from typing import Optional
from datetime import datetime
from pydantic import EmailStr, UUID4
from passlib.context import CryptContext

from ..model import ImmutBaseModel


# password = "secret"
fake_users_db = {
    "johndoe": {
        "uuid": "b316f0b4-0417-4e42-8c4b-89a4ed6b2da0",
        "full_name": "John Doe",
        "username": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
        "email_verified": True,
        "scopes": "",
        "created_at": "2021-02-27T19:18:54.567984",
    },
    "alice": {
        "uuid": "6073da24-7b23-4a2d-933f-05bc13b046e1",
        "username": "alice@example.com",
        "full_name": "Alice Wonderson",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": True,
        "email_verified": False,
        "scopes": "",
        "created_at": "2021-02-27T19:18:15.382777",
    },
}

# ["auto"] will configure the CryptContext instance to deprecate all
# supported schemes except for the default scheme.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", truncate_error=True)


class UserInDB(ImmutBaseModel):
    uuid: UUID4
    username: EmailStr
    full_name: str
    hashed_password: str
    disabled: bool = False
    email_verified: bool = False
    scopes: Optional[str] = None
    created_at: datetime


async def get_user(username: str) -> Optional[UserInDB]:
    user_dict = fake_users_db.get(username)
    if user_dict:
        return UserInDB(**user_dict)
    return None


async def autheticate_user(username: str, password: str) -> Optional[UserInDB]:
    user = await get_user(username)
    if not user:
        return None
    if not verify_password(username, password, user.hashed_password):
        return None
    return user


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


class UserDB:
    def __init__(self):
        self.db = {}

    def get(self, email: str):
        return self.db.get(email, None)

    def store(self, username: str, data: dict):
        self.db[username] = data
