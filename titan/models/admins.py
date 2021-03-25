from typing import Optional

from databases import Database

from ..exceptions.exc import DatabaseUserFetchError
from .pgsql import PgSQLTable
from .schema.admins import AdminInDB, admins_schema


class AdminsTable(PgSQLTable):
    def __init__(self, database_url: str, table_name: str):
        super().__init__(Database(database_url), admins_schema(admins_table=table_name))

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
