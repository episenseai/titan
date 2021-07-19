from typing import Optional

import sqlalchemy
from databases import Database
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.schema import Table

from ...logger import logger
from ..base import PgSQLBase


class PgSQLManageTable(PgSQLBase):
    def __init__(self, database: Database, table: Table):
        super().__init__(database, table)

    @property
    def db_context(self) -> str:
        return f"db={self.database.url}, tbl={self.table.name}"

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
            logger.error(
                f"checking 'pgcrypto' extension: ({self.db_context}, result={dict(result)}"
            )
            exit(1)
        return result.get("exists")

    async def create_pycrypto_extension(self):
        query = 'CREATE EXTENSION "pgcrypto"'
        logger.info(f"creating 'pgcrypto' extension: ({self.db_context})")
        await self.database.fetch_one(query=query)

    async def exists_trigger_set_timestamp(self) -> bool:
        query = "SELECT exists(SELECT * FROM pg_proc WHERE proname = 'trigger_set_timestamp');"

        result = await self.database.fetch_one(query=query)

        if result is None or not isinstance(result.get("exists"), bool):
            logger.error(
                f"checking 'trigger_set_timestamp()': ({self.db_context}, result={dict(result)})"
            )
            exit(1)
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
        logger.info(f"creating 'trigger_set_timestamp()': ({self.db_context})")
        await self.database.fetch_one(query=query)

    async def exists_table_in_db(self) -> bool:
        query = f"SELECT exists(SELECT * FROM pg_tables WHERE tablename = '{self.table.name}')"

        result = await self.database.fetch_one(query=query)

        if result is None or not isinstance(result.get("exists"), bool):
            logger.error(f"checking table exists: ({self.db_context}, result={dict(result)})")
            exit(1)
        return result.get("exists")

    async def create_table_in_db(self):
        query = sqlalchemy.schema.CreateTable(self.table)
        logger.info(f"creating table: ({self.db_context})")
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
            logger.error(
                f"checking exists col=updated_at: ({self.db_context}, result={dict(result)})"
            )
            exit(1)
        return result.get("exists")

    async def create_trigger_updated_at(self):
        query = f"""
        CREATE TRIGGER set_timestamp
        BEFORE UPDATE ON {self.table.name}
        FOR EACH ROW
        EXECUTE PROCEDURE trigger_set_timestamp();
        """
        logger.info(f"creating 'trigger_set_timestamp()': ({self.db_context}, col=updated_at)")
        return await self.database.fetch_one(query=query)

    async def create_table(self):
        exists = await self.exists_trigger_set_timestamp()
        if not exists:
            await self.create_trigger_set_timestamp()
            exists = await self.exists_trigger_set_timestamp()
            if not exists:
                logger.error(
                    f"creating 'trigger_set_timestamp()': ({self.db_context})",
                )
                exit(1)

        exists = await self.exists_pgcrypto_extension() or None
        if not exists:
            await self.create_pycrypto_extension()
            exists = await self.exists_pgcrypto_extension()
            if not exists:
                logger.error(f"creating 'pgcrypto' extension: ({self.db_context})")
                exit(1)

        exists = await self.exists_table_in_db() or None
        if not exists:
            await self.create_table_in_db()
            exists = await self.exists_table_in_db()
            if not exists:
                logger.error(f"creating table: ({self.db_context})")
                exit(1)
        else:
            logger.warn(f"table exists: ({self.db_context})")
            return

        exists = await self.exists_column_updated_at() or None
        if exists:
            try:
                await self.create_trigger_updated_at()
            except Exception as exc:
                logger.exception(f"creating 'trigger_set_timestamp()': ({self.db_context})")
        else:
            logger.info(f"exists 'trigger_set_timestamp()': ({self.db_context}, col=updated_at)")
