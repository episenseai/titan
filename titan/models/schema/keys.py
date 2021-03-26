from datetime import datetime
from typing import Optional

import sqlalchemy
from pydantic import UUID4
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql.schema import ForeignKey, Table

from ...utils import ImmutBaseModel


def keys_schema(keys_table: str, users_table: str) -> Table:
    """
    (keyid) is the primary key of this table
    """
    from .users import users_schema

    users_table = users_schema(users_table=users_table)

    metadata = sqlalchemy.MetaData()

    # Column defaults/onupdate callables are not supported by 'databases' library.
    # That is why we are using server_default/server_onupdate.

    # https://docs.sqlalchemy.org/en/13/core/metadata.html#sqlalchemy.schema.Column
    return sqlalchemy.Table(
        keys_table,
        metadata,
        # Unique id generated by the database.
        sqlalchemy.Column(
            "keyid",
            postgresql.UUID(),
            primary_key=True,
            server_default=sqlalchemy.text("uuid_generate_v4()"),
        ),
        # Foreign key 'userid' from 'users' tabel associated with each key.
        # Userid to which the key belongs
        sqlalchemy.Column(
            "userid",
            postgresql.UUID(),
            ForeignKey(users_table.c.userid),
            nullable=False,
        ),
        # Hash of the secret key. Send the original unhashed secret back to the client
        # when creating a new key, so that the client can use this secret to access
        # apis. Store only the salted hash of the key for verification.
        sqlalchemy.Column("keypass", sqlalchemy.String(length=1024), nullable=False),
        # Is the key disabled by the admin?
        sqlalchemy.Column(
            "frozen",
            sqlalchemy.Boolean,
            nullable=False,
            server_default=sqlalchemy.sql.expression.false(),
        ),
        # Is the key disabled by the user?. Reversible
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
        # Date of key creation
        sqlalchemy.Column(
            "created_at",
            sqlalchemy.DateTime(timezone=True),
            nullable=False,
            server_default=sqlalchemy.sql.functions.current_timestamp(),
        ),
        # Date of key update.
        sqlalchemy.Column(
            "updated_at",
            sqlalchemy.DateTime(timezone=True),
            nullable=False,
            server_default=sqlalchemy.sql.functions.current_timestamp(),
            # NOTE: this does not work in postgres, have to use trigger
            server_onupdate=sqlalchemy.sql.functions.current_timestamp(),
        ),
        # Optional description of the key.
        sqlalchemy.Column("description", sqlalchemy.String(length=255), nullable=True),
    )


class NewKey(ImmutBaseModel):
    keyid: UUID4
    userid: UUID4
    description: Optional[str] = None


class KeyInDB(ImmutBaseModel):
    keyid: UUID4
    userid: UUID4
    keypass: str
    frozen: bool
    disabled: bool
    deleted: bool
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None

    class Config:
        orm_mode = True


class AllKeysInDB(ImmutBaseModel):
    keys: list[KeyInDB]
