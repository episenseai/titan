from datetime import datetime
from uuid import uuid4
from typing import Optional

from passlib.context import CryptContext
from pydantic import UUID4

from ..models import ImmutBaseModel
from ..oauth2.models import IdP, OAuth2AuthentcatedUser

# ["auto"] will configure the CryptContext instance to deprecate all
# supported schemes except for the default scheme.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", truncate_error=True)

fake_users_db = {}


class UserInDB(ImmutBaseModel):
    idp: IdP
    provider_id: str
    # we create the account only when email is verified on the oauth2 provider side
    provider_email: str
    provider_username: str
    full_name: str
    uuid: UUID4
    disabled: bool = False
    scope: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # our own email verification
    email_verified: bool = False


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

    def get(self, auth_user: OAuth2AuthentcatedUser) -> UserInDB:
        return self.db.get((auth_user.provider_id, auth_user.idp), None)

    def create_user(self, auth_user: OAuth2AuthentcatedUser) -> UserInDB:
        uuid = uuid4()
        current_datettime = datetime.utcnow()
        default_scope = "episense:demo"

        user = UserInDB(
            **auth_user.dict(),
            uuid=uuid,
            disabled=False,
            scope=default_scope,
            created_at=current_datettime,
            updated_at=current_datettime,
            email_verified=False,
        )
        self.db[(auth_user.provider_id, auth_user.idp)] = user
        return user
