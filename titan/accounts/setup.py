from databases import Database
import asyncio
import sqlalchemy
from .schema import users

# from sqlalchemy.dialects import postgresql


# compiled CREATE TABLE statement
# print(str(sqlalchemy.schema.CreateTable(users).compile(dialect=postgresql.dialect())))

database = Database("postgresql://localhost/testdb")


async def setup_users_table(database: Database):
    async with database as db:
        uuid_enable_query = '''CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'''
        await db.execute(query=uuid_enable_query)

        create_table_query = sqlalchemy.schema.CreateTable(users)
        await db.execute(query=create_table_query)


asyncio.get_event_loop().run_until_complete(setup_users_table(database))
