from datetime import datetime
from typing import Optional

import sqlalchemy
from pydantic import UUID4
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.schema import ForeignKey, Table

from ...utils import ImmutBaseModel


def apis_schema(apis_table: str, users_table_name: str, keys_table_name: str) -> Table:
    """
    (apislug) is the primary key of this table

    *** After creating an API endpoint and associating a key with it for authentication,
        associate this endpoint with a built model to access the model through the
        endpoint. ***
    """
    from .keys import keys_schema
    from .users import users_schema

    users_table = users_schema(users_table=users_table_name)
    keys_table = keys_schema(keys_table=keys_table_name, users_table=users_table_name)

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
        # Foreign key 'keyid' from 'keys' table associated with each api.
        # Key used by the api for authentication. It may be null while creating the
        # api but a key must be associated at a later time time to use the api.
        sqlalchemy.Column(
            "keyid",
            postgresql.UUID(),
            ForeignKey(keys_table.c.keyid),
            # We can update this later.
            nullable=True,
        ),
        # Is the api disabled by the admin?
        sqlalchemy.Column(
            "forzen",
            sqlalchemy.Boolean,
            nullable=False,
            server_default=sqlalchemy.sql.expression.false(),
        ),
        # Is the api disabled by the user?
        sqlalchemy.Column(
            "disabled",
            sqlalchemy.Boolean,
            nullable=False,
            server_default=sqlalchemy.sql.expression.false(),
        ),
        # Deleting the api sets the field to `True`
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
            server_onupdate=sqlalchemy.sql.functions.current_timestamp(),
        ),
        # Optional description of the api.
        sqlalchemy.Column("description", sqlalchemy.String(length=255), nullable=True),
    )


class ApiInDB(ImmutBaseModel):
    apislug: str
    userid: UUID4
    keyid: UUID4
    frozen: bool
    disabled: bool
    deleted: bool
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None

    class Config:
        orm_mode = True
