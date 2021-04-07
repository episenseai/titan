from databases import Database

from ..schema.admins import admins_schema
from .base import PgSQLManageTable


class AdminsTableManage(PgSQLManageTable):
    def __init__(
        self,
        database: Database,
        admins_table: str,
    ) -> None:
        super().__init__(
            database=database,
            table=admins_schema(admins_table=admins_table),
        )
