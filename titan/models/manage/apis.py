from databases import Database

from ..schema.apis import apis_schema
from .base import PgSQLManageTable


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
