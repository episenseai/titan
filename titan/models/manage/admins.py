from databases import Database

from ..schema.admins import admins_schema
from .base import PgSQLManageTable


class AdminsTableManage(PgSQLManageTable):
    def __init__(
        self,
        database_url: str,
        admins_table: str,
        uuid_ext: bool = True,
    ) -> None:
        super().__init__(
            database=Database(database_url),
            table=admins_schema(admins_table=admins_table),
        )
