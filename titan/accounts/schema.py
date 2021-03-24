from datetime import datetime
from typing import Optional

import sqlalchemy
from asyncpg.exceptions import DuplicateTableError
from databases import Database
from pydantic import UUID4
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.schema import Table

from ..models import ImmutBaseModel
from ..oauth2.models import IDP


def users_schema(table_name: str) -> Table:
    """
    (email) is the primary key of this table

    NOTE:
        Reuse or `cache` the return value at the call site. Schema
        do not change except for during migrations.
    """
    metadata = sqlalchemy.MetaData()

    # https://docs.sqlalchemy.org/en/13/core/metadata.html#sqlalchemy.schema.Column
    return sqlalchemy.Table(
        table_name,
        metadata,
        sqlalchemy.Column(
            "userid",
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
        sqlalchemy.Column("idp_userid", sqlalchemy.String(length=128), nullable=False),
        sqlalchemy.Column("idp_username", sqlalchemy.String(length=128), nullable=True),
    )


class UserInDB(ImmutBaseModel):
    # Unique uuid4 generated by the database.
    userid: UUID4
    # We create the account only when email is verified on the oauth2
    # provider side.
    email: str
    # given_name + family_name
    full_name: Optional[str] = None
    # Account is disabled or not.
    disabled: bool
    # Did we verify the email ourselves. We are creating accounts
    # ony when the email is verified by the provider.
    email_verified: bool
    # Granted oauth2 `scope` to the user on our platform.
    scope: str = ""
    # profile picture if available.
    picture: Optional[str] = None
    # Date of account creation on our platform.
    created_at: datetime
    # Date the account info was last updated on our platform.
    updated_at: datetime
    # Identity Provider.
    idp: IDP
    # Unique Id of the the user that we get from identity provider.
    idp_userid: str
    # Optional username/login of the user from identity provider.
    idp_username: Optional[str] = None

    class Config:
        orm_mode = True


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
