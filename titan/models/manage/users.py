from databases import Database

from ..schema.users import users_schema
from .base import PgSQLManageTable


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
