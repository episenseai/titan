from typing import ClassVar, Optional

from asyncpg.exceptions import UniqueViolationError
from databases import Database
from passlib.context import CryptContext
from pydantic import UUID4

from ..base import PgSQLBase
from ..schema.admins import admins_schema
from ...logger import logger


class AdminsTableInternal(PgSQLBase):
    # 'bcrypt' truncates ones larger than 72 bytes. truncate_error=True will
    # raise a PasswordTruncateError.
    pwd_context: ClassVar[CryptContext] = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        truncate_error=True,
    )

    def __init__(
        self,
        database_url: str,
        admins_table: str,
    ) -> None:
        super().__init__(
            database=Database(database_url),
            table=admins_schema(admins_table=admins_table),
        )

    async def hash_password(self, password: str) -> Optional[str]:
        """
        Hash password using bcrypt
        """
        try:
            return self.pwd_context.hash(password)
        except Exception as exc:
            logger.error(f"Unexpected: Could not hash admin password: {exc}")
            return None

    async def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            return self.pwd_context.verify(password, password_hash)
        except Exception as exc:
            logger.error(f"Unexpected: Could not verify admin password: {exc}")
            return False

    async def create(self, email: str, username: str, password: str, scope: str) -> Optional[bool]:
        password_hash = await self.hash_password(password)
        if password_hash is None:
            return None
        value = {"email": email, "username": username, "password": password_hash, "scope": scope}
        query = (
            self.table.insert()
            .values(value)
            .returning(
                self.table.c.email,
                self.table.c.username,
            )
        )
        try:
            newadmin = await self.database.fetch_one(query=query)
        except UniqueViolationError:
            # admin already exists
            return False
        if newadmin is None:
            return None
        return True

    async def freeze_adminid(self, adminid: UUID4):
        return await self.toogle(frozen=True, adminid=adminid)

    async def unfreeze_adminid(self, adminid: UUID4):
        return await self.toogle(frozen=False, adminid=adminid)

    async def freeze_username(self, username: str):
        return await self.toogle(frozen=True, username=username)

    async def unfreeze_username(self, username: str):
        return await self.toogle(frozen=False, username=username)

    async def toogle(
        self,
        frozen: bool,
        adminid: Optional[UUID4] = None,
        username: Optional[str] = None,
    ) -> Optional[bool]:
        if adminid:
            partial_query = self.table.update().where(self.table.c.adminid == adminid)
        elif username:
            partial_query = self.table.update().where(self.table.c.username == username)
        else:
            # neither adminid nor email was provided
            return None

        query = partial_query.values({"frozen": frozen}).returning(self.table.c.frozen)

        result = await self.database.fetch_one(query=query)
        if result is None:
            # no matching row found
            return None
        if result.get("frozen") == frozen:
            # state has been successfully toggled.
            return True
        # this should never happen
        return False
