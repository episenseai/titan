from typing import Optional

import sqlalchemy
from databases import Database
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.schema import Table

from ..base import PgSQLBase


class PgSQLManageTable(PgSQLBase):
    def __init__(self, database: Database, table: Table):
        super().__init__(database, table)

    async def insert(self, values: Optional[dict] = None):
        await self.database.execute(query=self.table.insert(), values=values)

    async def str_schema(self) -> str:
        """
        Compiled `CREATE TABLE ...` statement
        """
        return sqlalchemy.schema.CreateTable(self.table).compile(dialect=postgresql.dialect())

    async def exists_pgcrypto_extension(self) -> bool:
        query = "SELECT exists(SELECT * FROM pg_extension WHERE extname = 'pgcrypto');"

        result = await self.database.fetch_one(query=query)

        if result is None or not isinstance(result.get("exists"), bool):
            raise RuntimeError(
                'Could not check whether "pgcrypto" extension exists: '
                + f"(database={self.database.url}, table={self.table.name}) query_result={dict(result)}"
            )
        return result.get("exists")

    async def create_pycrypto_extension(self):
        query = 'CREATE EXTENSION "pgcrypto"'
        print(
            f'Creating "pgcrypto" extension: (database={self.database.url}, table={self.table.name})',
        )
        await self.database.fetch_one(query=query)

    async def exists_trigger_set_timestamp(self) -> bool:
        query = "SELECT exists(SELECT * FROM pg_proc WHERE proname = 'trigger_set_timestamp');"

        result = await self.database.fetch_one(query=query)

        if result is None or not isinstance(result.get("exists"), bool):
            raise RuntimeError(
                "Could not check whether 'trigger_set_timestamp' function exists: "
                + f"(database={self.database.url}, table={self.table.name}) query_result={dict(result)}"
            )
        return result.get("exists")

    async def create_trigger_set_timestamp(self):
        query = """
        CREATE OR REPLACE FUNCTION trigger_set_timestamp()
        RETURNS TRIGGER AS $$
        BEGIN
          NEW.updated_at = CURRENT_TIMESTAMP;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
        print(
            f"Creating 'trigger_set_timestamp' function: (database={self.database.url}, table={self.table.name})",
        )
        await self.database.fetch_one(query=query)

    async def exists_table_in_db(self) -> bool:
        query = f"SELECT exists(SELECT * FROM pg_tables WHERE tablename = '{self.table.name}')"

        result = await self.database.fetch_one(query=query)

        if result is None or not isinstance(result.get("exists"), bool):
            raise RuntimeError(
                "Could not check the existence of table: "
                + f"(database={self.database.url}, table={self.table.name}) query_result={dict(result)}"
            )
        return result.get("exists")

    async def create_table_in_db(self):
        query = sqlalchemy.schema.CreateTable(self.table)
        print(f"Creating table: (database={self.database.url}, table={self.table.name})")
        await self.database.fetch_one(query=query)

    async def exists_column_updated_at(self) -> bool:
        query = f"""
        SELECT EXISTS(SELECT  column_name
                FROM  information_schema.columns
               WHERE  table_schema = 'public'
                 AND  table_name = '{self.table.name}'
                 AND  column_name = 'updated_at');
        """

        result = await self.database.fetch_one(query=query)

        if result is None or not isinstance(result.get("exists"), bool):
            raise RuntimeError(
                "Could not check the existence of column='updated_at': "
                + f"(database={self.database.url}, table={self.table.name}) query_result={dict(result)}"
            )
        return result.get("exists")

    async def create_trigger_updated_at(self):
        query = f"""
        CREATE TRIGGER set_timestamp
        BEFORE UPDATE ON {self.table.name}
        FOR EACH ROW
        EXECUTE PROCEDURE trigger_set_timestamp();
        """
        print(
            "Creating trigger 'trigger_set_timestamp()' for column='updated_at': "
            f"(database={self.database.url}, table={self.table.name})"
        )
        return await self.database.fetch_one(query=query)

    async def create_table(self):
        exists = await self.exists_trigger_set_timestamp()
        if not exists:
            await self.create_trigger_set_timestamp()
            exists = await self.exists_trigger_set_timestamp()
            if not exists:
                RuntimeError(
                    "Error creating 'trigger_set_timestamp' function: "
                    + f"(database={self.database.url}, table={self.table.name})",
                )

        exists = await self.exists_pgcrypto_extension()
        if not exists:
            await self.create_pycrypto_extension()
            exists = await self.exists_pgcrypto_extension()
            if not exists:
                RuntimeError(
                    'Error creating "pgcrypto" extension: '
                    + f"(database={self.database.url}, table={self.table.name})",
                )

        try:
            exists = await self.exists_table_in_db()
            if not exists:
                err_msg = (
                    "Error creating table in database: "
                    + f"(database={self.database.url}, table={self.table.name})",
                )
                await self.create_table_in_db()
                exists = await self.exists_table_in_db()
                if not exists:
                    RuntimeError(err_msg)
            else:
                print(
                    f"Table already exists: (database={self.database.url}, table={self.table.name})"
                )
                return
        except Exception as exc:
            RuntimeError(f"{err_msg}\n{exc}")

        exists = await self.exists_column_updated_at()
        if exists:
            try:
                await self.create_trigger_updated_at()
            except Exception as exc:
                RuntimeError(
                    "Error creating 'trigger_set_timestamp' function: "
                    + f"(database={self.database.url}, table={self.table.name})\n{exc}"
                )
        else:
            print(
                "Skipping creating 'trigger_set_timestamp()' for column='updated_at': "
                f"(database={self.database.url}, table={self.table.name})"
            )
