from typing import Optional

from databases import Database

from ..exceptions import DatabaseUserFetchError
from .pgsql import PgSQLTable
from .schema.keys import KeyInDB, keys_schema

# from passlib.context import CryptContext

# ["auto"] will configure the CryptContext instance to deprecate all
# supported schemes except for the default scheme.
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", truncate_error=True)


class KeysTable(PgSQLTable):
    def __init__(self, database_url: str, table_name: str, users_table_name: str) -> None:
        super().__init__(
            Database(database_url),
            keys_schema(keys_table=table_name, users_table=users_table_name),
        )
