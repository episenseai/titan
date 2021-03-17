import sqlalchemy
from asyncpg.exceptions import DuplicateTableError
from databases import Database
from sqlalchemy.dialects import postgresql

metadata = sqlalchemy.MetaData()

# https://docs.sqlalchemy.org/en/13/core/metadata.html#sqlalchemy.schema.Column
def users_schema(table_name: str):
    """
    (email) is the primary key of this table

    NOTE:
        Reuse or `cache` the return value at the call site. Schema
        do not change except for during migrations.
    """
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
        sqlalchemy.Column("full_name", sqlalchemy.String(length=254), nullable=True),
        sqlalchemy.Column("disabled", sqlalchemy.Boolean, nullable=False),
        sqlalchemy.Column("email_verified", sqlalchemy.Boolean, nullable=False),
        sqlalchemy.Column("scope", sqlalchemy.String(length=2048), nullable=False),
        sqlalchemy.Column("picture", sqlalchemy.String(length=2048), nullable=True),
        # Column defaults/onupdate callables are not supported by 'databases' library.
        # That is why we are using server_default/server_onupdate.
        sqlalchemy.Column(
            "created_at",
            sqlalchemy.DateTime(timezone=True),
            nullable=False,
            server_default=sqlalchemy.text("CURRENT_TIMESTAMP"),
        ),
        sqlalchemy.Column(
            "updated_at",
            sqlalchemy.DateTime(timezone=True),
            nullable=False,
            server_default=sqlalchemy.text("CURRENT_TIMESTAMP"),
            server_onupdate=sqlalchemy.text("CURRENT_TIMESTAMP"),
        ),
        sqlalchemy.Column("idp", sqlalchemy.String(length=32), nullable=False),
        sqlalchemy.Column("idp_guid", sqlalchemy.String(length=128), nullable=False),
        sqlalchemy.Column("idp_username", sqlalchemy.String(length=128), nullable=True),
    )


async def create_users_table(database: Database, table_name: str):
    """
    compiled CREATE TABLE statement
    >>> print(str(sqlalchemy.schema.CreateTable(users_table).compile(dialect=postgresql.dialect())))
    """
    async with database as db:
        try:
            # enable UUID extension for the postgresql
            uuid_enable_query = '''CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'''
            await db.execute(query=uuid_enable_query)
            users_table = users_schema(table_name)
            # CREATE TABLE
            create_table_query = sqlalchemy.schema.CreateTable(users_table)
            await db.execute(query=create_table_query)
        except DuplicateTableError as exc:
            print(f"{exc} -- TABLE already exists in the {database.url}")
