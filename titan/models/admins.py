from typing import Optional

from databases import Database

from ..exceptions.exc import DatabaseUserFetchError
from .schema.admins import AdminInDB, admins_schema

# from passlib.context import CryptContext

# ["auto"] will configure the CryptContext instance to deprecate all
# supported schemes except for the default scheme.
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", truncate_error=True)


class AdminsDB:
    def __init__(self, db_url: str, table_name: str):
        self.database = Database(db_url)
        self.table = admins_schema(table_name=table_name)

    async def connect(self):
        await self.database.connect()

    async def disconnect(self):
        await self.database.disconnect()

    async def get_admin(self, email: str, username: str) -> Optional[AdminInDB]:
        query = (
            self.table.select()
            .where(
                self.table.columns.email == email,
            )
            .where(
                self.table.columns.username == username,
            )
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

    @staticmethod
    async def verify_password(admin: AdminInDB, password: str) -> bool:
        if admin.password == password:
            return True
        return False
