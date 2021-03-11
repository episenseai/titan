from datetime import datetime
import sqlalchemy
from sqlalchemy.dialects import postgresql

metadata = sqlalchemy.MetaData()

# https://docs.sqlalchemy.org/en/13/core/metadata.html#sqlalchemy.schema.Column
users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column(
        "guid",
        postgresql.UUID(as_uuid=True),
        nullable=False,
        unique=True,
        server_default=sqlalchemy.text("uuid_generate_v4()"),
    ),
    sqlalchemy.Column("email", sqlalchemy.String(length=254), primary_key=True),
    sqlalchemy.Column("full_name", sqlalchemy.String(length=254), nullable=False),
    sqlalchemy.Column("disabled", sqlalchemy.Boolean, nullable=False),
    sqlalchemy.Column("email_verified", sqlalchemy.Boolean, nullable=False),
    sqlalchemy.Column("scope", sqlalchemy.String(length=2048), nullable=False),
    sqlalchemy.Column("picture", sqlalchemy.String(length=2048), nullable=True),
    sqlalchemy.Column(
        "created_at",
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow(),
    ),
    sqlalchemy.Column(
        "updated_at",
        sqlalchemy.DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow(),
        onupdate=datetime.utcnow(),
    ),
    sqlalchemy.Column("idp", sqlalchemy.String(length=32), nullable=False),
    sqlalchemy.Column("idp_guid", sqlalchemy.String(length=128), nullable=False),
    sqlalchemy.Column("idp_username", sqlalchemy.String(length=128), nullable=True),
)
