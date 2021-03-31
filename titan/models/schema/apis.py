from datetime import datetime
from typing import Optional

import sqlalchemy
from pydantic import UUID4
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.schema import ForeignKey, Table

from ...utils import ImmutBaseModel


def apis_schema(apis_table: str, users_table: str) -> Table:
    """
    (apislug) is the primary key of this table

    *** After creating an API endpoint and associating a key with it for authentication,
        associate this endpoint with a built model to access the model through the
        endpoint. ***
    """
    from .users import users_schema

    users_table = users_schema(users_table=users_table)

    metadata = sqlalchemy.MetaData()

    # Column defaults/onupdate callables are not supported by 'databases' library.
    # That is why we are using server_default/server_onupdate.

    # https://docs.sqlalchemy.org/en/13/core/metadata.html#sqlalchemy.schema.Column
    return sqlalchemy.Table(
        apis_table,
        metadata,
        # urlencoded string to be used as 'slug' in the url to access the api
        # https://models.episense.com/{userid}/{apislug}
        sqlalchemy.Column(
            "apislug",
            sqlalchemy.String(length=128),
            primary_key=True,
        ),
        # Foreign key 'userid' from 'users' table associated with each api.
        # User to which the api belongs
        sqlalchemy.Column(
            "userid",
            postgresql.UUID(),
            ForeignKey(users_table.c.userid),
            nullable=False,
        ),
        # Hash of the secret key. Send the original unhashed secret back to the client
        # when creating a new key, so that the client can use this secret to access
        # apis. Store only the salted hash of the key for verification.
        sqlalchemy.Column("secret_hash", sqlalchemy.String(length=1024), nullable=False),
        # Is the api disabled by the admin?
        sqlalchemy.Column(
            "frozen",
            sqlalchemy.Boolean,
            nullable=False,
            server_default=sqlalchemy.sql.expression.false(),
        ),
        # Is the api disabled by the user? Reversible
        sqlalchemy.Column(
            "disabled",
            sqlalchemy.Boolean,
            nullable=False,
            server_default=sqlalchemy.sql.expression.false(),
        ),
        # After marking it for deletion it can not be undone.
        sqlalchemy.Column(
            "deleted",
            sqlalchemy.Boolean,
            nullable=False,
            server_default=sqlalchemy.sql.expression.false(),
        ),
        # Date of api creation
        sqlalchemy.Column(
            "created_at",
            sqlalchemy.DateTime(timezone=True),
            nullable=False,
            server_default=sqlalchemy.sql.functions.current_timestamp(),
        ),
        # Date of api update.
        sqlalchemy.Column(
            "updated_at",
            sqlalchemy.DateTime(timezone=True),
            nullable=False,
            server_default=sqlalchemy.sql.functions.current_timestamp(),
            # NOTE: this does not work in postgres, have to use trigger
            server_onupdate=sqlalchemy.sql.functions.current_timestamp(),
        ),
        # Optional description of the api.
        sqlalchemy.Column("description", sqlalchemy.String(length=255), nullable=False),
    )


class NewAPI(ImmutBaseModel):
    apislug: str
    userid: UUID4
    client_secret: str
    description: Optional[str] = None


class APIInDB(ImmutBaseModel):
    apislug: str
    userid: UUID4
    secret_hash: str
    frozen: bool
    disabled: bool
    deleted: bool
    created_at: datetime
    updated_at: datetime
    description: str

    class Config:
        orm_mode = True


class AllAPIsInDB(ImmutBaseModel):
    apis: list[APIInDB]
