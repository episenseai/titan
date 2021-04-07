from databases import Database

from ..schema.users import users_schema
from .base import PgSQLManageTable


class UsersTableManage(PgSQLManageTable):
    def __init__(
        self,
        database: Database,
        users_table: str,
    ) -> None:
        super().__init__(
            database=database,
            table=users_schema(users_table=users_table),
        )
