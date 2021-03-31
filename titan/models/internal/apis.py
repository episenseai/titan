from databases import Database

from ..base import PgSQLBase
from ..schema.apis import apis_schema


class APIsTableInternal(PgSQLBase):
    def __init__(
        self,
        database_url: str,
        apis_table: str,
        users_table: str,
    ) -> None:
        super().__init__(
            database=Database(database_url),
            table=apis_schema(apis_table=apis_table, users_table=users_table),
        )

    async def freeze(self, apislug: str):
        # TODO
        pass

    async def unfreeze(self, apislug: str):
        # TODO
        pass
