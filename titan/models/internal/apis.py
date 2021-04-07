from typing import Optional

from databases import Database
from pydantic import UUID4

from ..base import PgSQLBase
from ..schema.apis import AllAPIsInDB, apis_schema


class APIsTableInternal(PgSQLBase):
    def __init__(
        self,
        database: Database,
        apis_table: str,
        users_table: str,
    ) -> None:
        super().__init__(
            database=database,
            table=apis_schema(apis_table=apis_table, users_table=users_table),
        )

    async def get_all(self, userid: UUID4) -> AllAPIsInDB:
        """
        Get all apis, including 'frozen' and 'deleted', since this is the admin interface.
        """
        query = self.table.select().where(self.table.c.userid == userid)
        records = await self.database.fetch_all(query=query)
        if not records:
            return AllAPIsInDB(apis=[])
        return AllAPIsInDB(apis=({**record} for record in records))

    async def toogle(self, userid: UUID4, apislug: str, frozen: bool) -> Optional[bool]:
        query = (
            self.table.update()
            .where(self.table.c.userid == userid)
            .where(self.table.c.apislug == apislug)
            .values({"frozen": frozen})
            .returning(self.table.c.frozen)
        )
        result = await self.database.fetch_one(query=query)
        if result is None:
            # no matching row found
            return None
        if result.get("frozen") == frozen:
            # state has been successfully toggled.
            return True
        # this should never happen
        return False

    async def freeze(self, userid: UUID4, apislug: str) -> Optional[bool]:
        """
        Freeze the api. After being frozen the api is disabled and the user
        can not take any action on it.
        """
        return await self.toogle(userid, apislug, frozen=True)

    async def unfreeze(self, userid: UUID4, apislug: UUID4) -> Optional[bool]:
        return await self.toogle(userid, apislug, frozen=False)
