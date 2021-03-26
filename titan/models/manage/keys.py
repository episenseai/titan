from databases import Database

from ..schema.keys import keys_schema
from .base import PgSQLManageTable


class KeysTableManage(PgSQLManageTable):
    def __init__(
        self,
        database_url: str,
        keys_table: str,
        users_table: str,
        uuid_ext: bool = True,
    ) -> None:
        super().__init__(
            database=Database(database_url),
            table=keys_schema(
                keys_table=keys_table,
                users_table=users_table,
            ),
            uuid_ext=uuid_ext,
        )
