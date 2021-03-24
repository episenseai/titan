from datetime import datetime
from typing import Optional

import sqlalchemy
from asyncpg.exceptions import DuplicateTableError
from databases import Database
from pydantic import UUID4
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.schema import ForeignKey, Table

from ..models import ImmutBaseModel


def apis_schema(table_name: str, users_table_name: str, keys_table_name: str) -> Table:
    """
    (apislug) is the primary key of this table
    """
    from ..accounts.schema import users_schema
    from .keys_schema import keys_schema

    users_table = users_schema(table_name=users_table_name)
    keys_table = keys_schema(table_name=keys_table_name)

    metadata = sqlalchemy.MetaData()

    # https://docs.sqlalchemy.org/en/13/core/metadata.html#sqlalchemy.schema.Column
    return sqlalchemy.Table(
        table_name,
        metadata,
        # urlencoded string to be used as 'slug' in the url to access the api
        sqlalchemy.Column(
            "apislug",
            sqlalchemy.String(length=128),
            nullable=False,
            unique=True,
        ),
        # Foreign key 'userid' from 'users' table associated with each api.
        sqlalchemy.Column(
            "userid",
            postgresql.UUID(),
            ForeignKey(users_table.c.userid),
            nullable=False,
        ),
        # Foreign key 'keyid' from 'keys' table associated with each api.
        sqlalchemy.Column(
            "keyid",
            postgresql.UUID(),
            ForeignKey(keys_table.c.keyid),
            # We can update this later.
            nullable=True,
        ),
        sqlalchemy.Column("disabled", sqlalchemy.Boolean, nullable=False),
        sqlalchemy.Column("deleted", sqlalchemy.Boolean, nullable=False),
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
        sqlalchemy.Column("description", sqlalchemy.String(length=255), nullable=True),
    )


class ApiInDB(ImmutBaseModel):
    # Unique slug for the api.
    # https://models.episense.com/{userid}/{apislug}
    apislug: str
    # User to which the api belongs
    userid: UUID4
    # Key used by the api for authentication. It may be null while creating the
    # api but a key must be associated at a later time time to use the api.
    keyid: UUID4
    # Disable the key.
    disabled: bool
    # Deleting the key sets the field to `True`
    deleted: bool
    # Date of api creation
    created_at: datetime
    # Date of api update.
    created_at: datetime
    # Optional description of the key.
    description: Optional[str] = None

    class Config:
        orm_mode = True


async def create_apis_table(database: Database, table_name: str, users_table_name: str, keys_table_name: str):
    """
    compiled CREATE TABLE statement
    >>> print(str(sqlalchemy.schema.CreateTable(apis_table).compile(dialect=postgresql.dialect())))
    """
    async with database as db:
        try:
            # enable UUID extension for the postgresql
            uuid_enable_query = '''CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'''
            await db.execute(query=uuid_enable_query)
            apis_table = apis_schema(
                table_name=table_name, users_table_name=users_table_name, keys_table_name=keys_table_name
            )
            # CREATE TABLE
            create_table_query = sqlalchemy.schema.CreateTable(apis_table)
            await db.execute(query=create_table_query)
        except DuplicateTableError as exc:
            print(f"{exc} -- TABLE already exists in the {database.url}")
