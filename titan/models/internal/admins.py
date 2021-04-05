from typing import Optional

from asyncpg.exceptions import UniqueViolationError
from databases import Database
from pydantic import UUID4

from ..base import PgSQLBase
from ..schema.admins import admins_schema


class AdminsTableInternal(PgSQLBase):
    def __init__(
        self,
        database_url: str,
        admins_table: str,
    ) -> None:
        super().__init__(
            database=Database(database_url),
            table=admins_schema(admins_table=admins_table),
        )

    async def create(self, value: dict) -> Optional[bool]:
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
