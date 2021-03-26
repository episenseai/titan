from typing import Optional

from databases import Database
from pydantic import UUID4

from ..base import PgSQLBase
from ..schema.keys import AllKeysInDB, keys_schema


class KeysTableInternal(PgSQLBase):
    def __init__(
        self,
        database_url: str,
        keys_table: str,
        users_table: str,
    ) -> None:
        super().__init__(
            database=Database(database_url),
            table=keys_schema(
                keys_table=keys_table,
                users_table=users_table,
            ),
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
