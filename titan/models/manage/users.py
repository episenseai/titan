from databases import Database

from ..schema.users import users_schema
from .base import PgSQLManageTable


class UsersTableManage(PgSQLManageTable):
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
