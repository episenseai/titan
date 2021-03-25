from datetime import datetime
from typing import Optional

import sqlalchemy
from pydantic import UUID4
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.schema import Table

from ...auth.models import IDP
from ...utils import ImmutBaseModel


def users_schema(users_table: str) -> Table:
    """
    (email) is the primary key of this table

    NOTE:
        Reuse or `cache` the return value at the call site. Schema
        do not change except for during migrations.
    """
    metadata = sqlalchemy.MetaData()

    # Column defaults/onupdate callables are not supported by 'databases' library.
    # That is why we are using server_default/server_onupdate.

    # https://docs.sqlalchemy.org/en/13/core/metadata.html#sqlalchemy.schema.Column
    return sqlalchemy.Table(
        users_table,
        metadata,
        # Unique id of the user generated by the database.
        sqlalchemy.Column(
            "userid",
            postgresql.UUID(),
            nullable=False,
            unique=True,
            server_default=sqlalchemy.text("uuid_generate_v4()"),
        ),
        # We create the account only when email is verified on the oauth2 provider side.
        sqlalchemy.Column("email", sqlalchemy.String(length=254), primary_key=True),
        # given_name + family_name
        sqlalchemy.Column("full_name", sqlalchemy.String(length=254), nullable=True),
        # Is the account disabled by the admin?
        sqlalchemy.Column(
            "forzen",
            sqlalchemy.Boolean,
            nullable=False,
            server_default=sqlalchemy.sql.expression.false(),
        ),
        # Did we verify the email ourselves (not the provider verification)? We are
        # creating accounts only when the email is verified by the provider.
        sqlalchemy.Column(
            "email_verified",
            sqlalchemy.Boolean,
            nullable=False,
            server_default=sqlalchemy.sql.expression.false(),
        ),
        # Granted oauth2 `scope` to the user by us (not the scope of the id provider)
        sqlalchemy.Column("scope", sqlalchemy.String(length=2048), nullable=False),
        # profile picture if available.
        sqlalchemy.Column("picture", sqlalchemy.String(length=2048), nullable=True),
        # Date of account creation.
        sqlalchemy.Column(
            "created_at",
            sqlalchemy.DateTime(timezone=True),
            nullable=False,
            server_default=sqlalchemy.sql.functions.current_timestamp(),
        ),
        # Date the account update.
        sqlalchemy.Column(
            "updated_at",
            sqlalchemy.DateTime(timezone=True),
            nullable=False,
            server_default=sqlalchemy.sql.functions.current_timestamp(),
            server_onupdate=sqlalchemy.sql.functions.current_timestamp(),
        ),
        # Identity Provider.
        sqlalchemy.Column("idp", sqlalchemy.String(length=32), nullable=False),
        # Unique Id of the the user that we get from the identity provider.
        sqlalchemy.Column("idp_userid", sqlalchemy.String(length=128), nullable=False),
        # Optional username/login of the user from identity provider.
        sqlalchemy.Column("idp_username", sqlalchemy.String(length=128), nullable=True),
    )


class UserInDB(ImmutBaseModel):
    userid: UUID4
    email: str
    full_name: Optional[str] = None
    forzen: bool
    email_verified: bool
    scope: str = ""
    picture: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    idp: IDP
    idp_userid: str
    idp_username: Optional[str] = None

    class Config:
        orm_mode = True
