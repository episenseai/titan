from typing import ClassVar, Optional

import sqlalchemy
from asyncpg.exceptions import DuplicateTableError
from databases import Database
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.schema import Table

from ..base import PgSQLBase


class PgSQLManageTable(PgSQLBase):
    # enable UUID extension for the postgresql
    uuid_enable_query: ClassVar[str] = '''CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'''

    def __init__(self, database: Database, table: Table, uuid_ext: bool = True):
        self.uuid_ext = uuid_ext
        super().__init__(database, table)

    def str_schema(self) -> str:
        """
        compiled CREATE TABLE statement
        """
        return sqlalchemy.schema.CreateTable(self.table).compile(dialect=postgresql.dialect())

    async def insert(self, values: Optional[dict] = None):
        await self.database.execute(query=self.table.insert(), values=values)

    async def create_table(self):
        try:
            if self.uuid_ext:
                # enable UUID extension
                await self.database.execute(query=self.uuid_enable_query)
            # CREATE TABLE
            await self.database.execute(query=sqlalchemy.schema.CreateTable(self.table))
        except DuplicateTableError as exc:
            print(f"{exc} -- TABLE already exists in the {self.database.url}")
