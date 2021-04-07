from typing import ClassVar, Optional

from databases import Database
from passlib.context import CryptContext

from ...exceptions.exc import DatabaseUserFetchError
from ...logger import logger
from ..base import PgSQLBase
from ..schema.admins import AdminInDB, admins_schema


class AdminsTable(PgSQLBase):
    # 'bcrypt' truncates ones larger than 72 bytes. truncate_error=True will
    # raise a PasswordTruncateError.
    pwd_context: ClassVar[CryptContext] = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        truncate_error=True,
    )

    def __init__(self, database: Database, admins_table: str):
        super().__init__(database=database, table=admins_schema(admins_table=admins_table))

    async def get_admin(self, email: str, username: str) -> Optional[AdminInDB]:
        query = (
            self.table.select().where(self.table.columns.email == email).where(self.table.columns.username == username)
        )
        # returns None if the admin is not in DB
        admin = await self.database.fetch_one(query=query)

        if admin is not None:
            try:
                return AdminInDB(**admin)
            except Exception as exc:
                print(f"Error {admin=} for {email=} {username=}")
                raise DatabaseUserFetchError from exc
        return None

    async def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            return self.pwd_context.verify(password, password_hash)
        except Exception as exc:
            logger.error(f"Unexpected: Could not verify admin password: {exc}")
            return False
