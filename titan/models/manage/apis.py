from databases import Database

from ..schema.apis import apis_schema
from .base import PgSQLManageTable


class APIsTableManage(PgSQLManageTable):
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
