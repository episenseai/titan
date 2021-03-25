from databases import Database
from sqlalchemy.sql.schema import Table


class PgSQLTable:
    def __init__(self, database: Database, table: Table) -> None:
        self.database = database
        self.table = table

    async def connect(self):
        """
        NOTE: Not required when executing in `async with` context
        """
        await self.database.connect()

    async def disconnect(self):
        """
        NOTE: Not required when executing in `async with` context
        """
        await self.database.disconnect()
