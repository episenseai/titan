from databases import Database
from sqlalchemy.sql.schema import Table


class PgSQLBase:
    """
    Do not mix `async with` and manually doing `self.connect()` and
    `self.disconnect()`

    :Example:
        >>> async def func():
        ...     pg = PgSQLBase(...)
        ...     await pg.connect()
        ...     await do_something(...)
        ...     await pg.disconnect(...)

    :Example:
        >>> async with PgSQLBase(...):
        ...     await ...
    """

    def __init__(self, database: Database, table: Table):
        self.database = database
        self.table = table

    async def connect(self):
        await self.database.connect()

    async def disconnect(self):
        await self.database.disconnect()

    async def __aenter__(self):
        await self.connect()

    async def __aexit__(self, exc_type=None, exc_value=None, traceback=None):
        await self.disconnect()
