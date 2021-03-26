from typing import ClassVar, Optional

import sqlalchemy
from asyncpg.exceptions import DuplicateTableError
from databases import Database
from pydantic import UUID4
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.schema import Table

from .schema.admins import admins_schema
from .schema.apis import apis_schema
from .schema.keys import AllKeysInDB, keys_schema
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


class UsersPgSQlManageTable(PgSQLManageTable):
    def __init__(
        self,
        database_url: str,
        users_table: str,
        uuid_ext: bool = True,
    ) -> None:
        super().__init__(
            database=Database(database_url),
            table=users_schema(users_table=users_table),
            uuid_ext=uuid_ext,
        )

    async def freeze_userid(self, userid: str):
        # TODO
        pass

    async def unfreeze_userid(self, userid: str):
        # TODO
        pass

    async def freeze_email(self, email: str):
        # TODO
        pass

    async def unfreeze_email(self, email: str):
        # TODO
        pass


class AdminsPgSQlManageTable(PgSQLManageTable):
    def __init__(
        self,
        database_url: str,
        admins_table: str,
        uuid_ext: bool = True,
    ) -> None:
        super().__init__(
            database=Database(database_url),
            table=admins_schema(admins_table=admins_table),
            uuid_ext=uuid_ext,
        )

    async def freeze_adminid(self, adminid: str):
        # TODO
        pass

    async def unfreeze_adminid(self, adminid: str):
        # TODO
        pass

    async def freeze_username(self, username: str):
        # TODO
        pass

    async def unfreeze_username(self, username: str):
        # TODO
        pass

    async def freeze_email(self, email: str):
        """
        Freeze all 'username' associated with this email.
        """
        # TODO
        pass

    def unfreeze_email(self, email: str):
        """
        Freeze all 'username' associated with this email.
        """
        # TODO
        pass


class KeysPgSQlManageTable(PgSQLManageTable):
    def __init__(
        self,
        database_url: str,
        keys_table: str,
        users_table: str,
        uuid_ext: bool = True,
    ) -> None:
        super().__init__(
            database=Database(database_url),
            table=keys_schema(
                keys_table=keys_table,
                users_table=users_table,
            ),
            uuid_ext=uuid_ext,
        )

    async def get_all(self, userid: UUID4) -> AllKeysInDB:
        """
        Get all keys 'frozen' or not since this is the admin interface.
        """
        query = self.table.select().where(self.table.c.userid == userid)
        records = await self.database.fetch_all(query=query)
        if not records:
            return AllKeysInDB(keys=[])
        return AllKeysInDB(keys=({**record} for record in records))

    async def toogle_frozen(self, userid: UUID4, keyid: UUID4, frozen: bool) -> Optional[bool]:
        query = (
            self.table.update()
            .where(self.table.c.userid == userid)
            .where(self.table.c.keyid == keyid)
            .values({"frozen": frozen})
            .returning(self.table.c.frozen)
        )
        result = await self.database.fetch_one(query=query)
        if result is None:
            # no matching row found
            return None
        if result.get("frozen") == (not frozen):
            # expected that the state the toogled
            return True
        # it was already toogled
        return False

    async def freeze(self, userid: UUID4, keyid: UUID4):
        return await self.toogle_frozen(userid, keyid, frozen=True)

    async def unfreeze(self, userid: UUID4, keyid: UUID4):
        return await self.toogle_frozen(userid, keyid, frozen=False)


class ApisPgSQlManageTable(PgSQLManageTable):
    def __init__(
        self,
        database_url: str,
        apis_table: str,
        users_table: str,
        keys_table: str,
        uuid_ext: bool = True,
    ) -> None:
        super().__init__(
            database=Database(database_url),
            table=apis_schema(
                apis_table=apis_table,
                users_table_name=users_table,
                keys_table_name=keys_table,
            ),
            uuid_ext=uuid_ext,
        )

    async def freeze(self, apislug: str):
        # TODO
        pass

    async def unfreeze(self, apislug: str):
        # TODO
        pass
