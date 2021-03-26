from databases import Database

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
