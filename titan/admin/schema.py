import sqlalchemy
from databases import Database
from asyncpg.exceptions import DuplicateTableError
from sqlalchemy.dialects import postgresql

metadata = sqlalchemy.MetaData()


def admins_schema(table_name: str):
    """
    (email + username) constitutes the primary key for the table.
    Same `email` may have have multiple accounts (username) with varying
    level of scopes.

    NOTE:
        Reuse or `cache` the return value at the call site. Schema
        do not change except for during migrations.
    """
    # https://docs.sqlalchemy.org/en/13/core/metadata.html#sqlalchemy.schema.Column
    return sqlalchemy.Table(
        table_name,
        metadata,
        sqlalchemy.Column(
            "guid",
            postgresql.UUID(),
            nullable=False,
            unique=True,
            server_default=sqlalchemy.text("uuid_generate_v4()"),
        ),
        sqlalchemy.Column("email", sqlalchemy.String(length=254), primary_key=True),
        sqlalchemy.Column("username", sqlalchemy.String(length=254), primary_key=True),
        sqlalchemy.Column("password", sqlalchemy.String(length=1024), nullable=False),
        sqlalchemy.Column("disabled", sqlalchemy.Boolean, nullable=False),
        sqlalchemy.Column("scope", sqlalchemy.String(length=2048), nullable=False),
        # Column defaults/onupdate callables are not supported by 'databases' library.
        # That is why we are using server_default/server_onupdate.
        sqlalchemy.Column(
            "created_at",
            sqlalchemy.DateTime(timezone=True),
            nullable=False,
            server_default=sqlalchemy.text("CURRENT_TIMESTAMP"),
        ),
    )


async def create_admins_table(database: Database, table_name: str):
    """
    compiled CREATE TABLE statement
    >>> print(str(sqlalchemy.schema.CreateTable(admins_table).compile(dialect=postgresql.dialect())))
    """
    async with database as db:
        try:
            # enable UUID extension for the postgresql
            uuid_enable_query = '''CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'''
            await db.execute(query=uuid_enable_query)
            admins_table = admins_schema(table_name)
            # CREATE TABLE
            create_table_query = sqlalchemy.schema.CreateTable(admins_table)
            await db.execute(query=create_table_query)
        except DuplicateTableError as exc:
            print(f"{exc} -- TABLE already exists in the {database.url}")
