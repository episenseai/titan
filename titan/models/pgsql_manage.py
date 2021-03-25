from typing import ClassVar, Optional

import sqlalchemy
from asyncpg.exceptions import DuplicateTableError
from databases import Database
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.schema import Table

from .schema.admins import admins_schema
from .schema.apis import apis_schema
from .schema.keys import keys_schema
from .schema.users import users_schema


class PgSQLManageTable:
    # enable UUID extension for the postgresql
    uuid_enable_query: ClassVar[str] = '''CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'''

    def __init__(self, database: Database, table: Table, uuid_ext: bool = True) -> None:
        self.database = database
        self.table = table
        self.uuid_ext = uuid_ext

    def str_schema(self) -> str:
        """
        compiled CREATE TABLE statement
        """
        return sqlalchemy.schema.CreateTable(self.table).compile(dialect=postgresql.dialect())

    async def connect(self):
        """
        NOTE: Not required when executing in `async with` context
        """
        await self.database.connect()

    async def disconnect(self):
        """
        NOTE: Not required when executing in `async with` context
        """
        await self.database.disconnect()

    async def insert(self, values: Optional[dict] = None):
        async with self.database as db:
            await db.execute(query=self.table.insert(), values=values)

    async def create_table(self):
        try:
            # connects with the database
            async with self.database as db:
                if self.uuid_ext:
                    # enable UUID extension
                    await db.execute(query=self.uuid_enable_query)
                # CREATE TABLE
                await db.execute(query=sqlalchemy.schema.CreateTable(self.table))
        except DuplicateTableError as exc:
            print(f"{exc} -- TABLE already exists in the {self.database.url}")


class UsersPgSQlManageTable(PgSQLManageTable):
    def __init__(
        self,
        database_url: str,
        table_name: str,
        uuid_ext: bool = True,
    ) -> None:
        super().__init__(
            database=Database(database_url),
            table=users_schema(table_name=table_name),
            uuid_ext=uuid_ext,
        )


class AdminsPgSQlManageTable(PgSQLManageTable):
    def __init__(
        self,
        database_url: str,
        table_name: str,
        uuid_ext: bool = True,
    ) -> None:
        super().__init__(
            database=Database(database_url),
            table=admins_schema(table_name=table_name),
            uuid_ext=uuid_ext,
        )


class KeysPgSQlManageTable(PgSQLManageTable):
    def __init__(
        self,
        database_url: str,
        table_name: str,
        users_table_name: str,
        uuid_ext: bool = True,
    ) -> None:
        super().__init__(
            database=Database(database_url),
            table=keys_schema(
                table_name=table_name,
                users_table_name=users_table_name,
            ),
            uuid_ext=uuid_ext,
        )


class ApisPgSQlManageTable(PgSQLManageTable):
    def __init__(
        self,
        database_url: str,
        table_name: str,
        users_table_name: str,
        keys_table_name: str,
        uuid_ext: bool = True,
    ) -> None:
        super().__init__(
            database=Database(database_url),
            table=apis_schema(
                table_name=table_name,
                users_table_name=users_table_name,
                keys_table_name=keys_table_name,
            ),
            uuid_ext=uuid_ext,
        )
