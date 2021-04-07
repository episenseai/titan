from databases import Database
from sqlalchemy.sql.schema import Table


class PgSQLBase:
    def __init__(self, database: Database, table: Table):
        self.database = database
        self.table = table
