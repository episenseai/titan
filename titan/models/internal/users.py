from typing import Optional

from databases import Database
from pydantic import UUID4

from ..base import PgSQLBase
from ..schema.users import users_schema


class UsersTableInternal(PgSQLBase):
    def __init__(
        self,
        database_url: str,
        users_table: str,
    ) -> None:
        super().__init__(
            database=Database(database_url),
            table=users_schema(users_table=users_table),
        )

    async def freeze_userid(self, userid: UUID4):
        return await self.toogle(frozen=True, userid=userid)

    async def unfreeze_userid(self, userid: UUID4):
        return await self.toogle(frozen=False, userid=userid)

    async def freeze_email(self, email: str):
        return await self.toogle(frozen=True, email=email)

    async def unfreeze_email(self, email: str):
        return await self.toogle(frozen=False, email=email)

    async def toogle(
        self,
        frozen: bool,
        userid: Optional[UUID4] = None,
        email: Optional[str] = None,
    ) -> Optional[bool]:
        if userid:
            partial_query = self.table.update().where(self.table.c.userid == userid)
        elif email:
            partial_query = self.table.update().where(self.table.c.email == email)
        else:
            # neither userid nor email was provided
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

    async def freeze(self, userid: UUID4, apislug: str):
        """
        Freeze the api. After being frozen the api is disabled and the user
        can not take any action on it.
        """
        return await self.toogle(userid, apislug, frozen=True)

    async def unfreeze(self, userid: UUID4, apislug: UUID4):
        return await self.toogle(userid, apislug, frozen=False)
