from databases import Database

from ..schema.apis import apis_schema
from .base import PgSQLManageTable


class APIsTableManage(PgSQLManageTable):
    def __init__(
        self,
        database_url: str,
        apis_table: str,
        users_table: str,
        uuid_ext: bool = True,
    ) -> None:
        super().__init__(
            database=Database(database_url),
            table=apis_schema(apis_table=apis_table, users_table=users_table),
        )
