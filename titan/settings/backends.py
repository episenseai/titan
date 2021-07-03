from databases import Database

from ..auth.state import StateTokensDB
from ..models.internal import AdminsTableInternal, APIsTableInternal, UsersTableInternal
from ..models.manage import AdminsTableManage, APIsTableManage, UsersTableManage
from ..models.public import AdminsTable, APIsTable, UsersTable
from .env import ADMINS_TABLE, APIS_TABLE, USERS_TABLE, env
from .idp import google_auth_client

postgres_database = Database(
    url=env().postgres_url,
    user=env().POSTGRESQL_USER,
    password=env().POSTGRESQL_PASSWORD.get_secret_value(),
)

users_db = UsersTable(postgres_database, USERS_TABLE)
users_db_internal = UsersTableInternal(postgres_database, USERS_TABLE)

admins_db = AdminsTable(postgres_database, ADMINS_TABLE)
admins_db_internal = AdminsTableInternal(postgres_database, ADMINS_TABLE)

apis_db = APIsTable(postgres_database, APIS_TABLE, USERS_TABLE)
apis_db_internal = APIsTableInternal(postgres_database, APIS_TABLE, USERS_TABLE)


async def check_table_existence():
    dbs = []

    dbs.append(UsersTableManage(postgres_database, USERS_TABLE))
    dbs.append(AdminsTableManage(postgres_database, ADMINS_TABLE))
    dbs.append(APIsTableManage(postgres_database, APIS_TABLE, USERS_TABLE))

    for db in dbs:
        exists = await db.exists_table_in_db()
        if not exists:
            raise RuntimeError(
                f"Table missing: (database={db.database.url}, table={db.table.name})"
            )


async def initialize_JWKS_keys():
    """
    Run this in production to aovid fetching keys over and over again
    """
    if google_auth_client.jwks_uri is None:
        raise RuntimeError("Google missing JWKS uri: needed for GoogleAuthClient")
    try:
        await google_auth_client.update_jwks_keys()
    except Exception:
        raise RuntimeError("Could not download JWKS keys from Google")


state_tokens_db = StateTokensDB(
    redis_host=env().REDIS_HOST,
    redis_port=env().REDIS_PORT,
    redis_password=env().REDIS_PASSWORD.get_secret_value(),
    redis_db=env().REDIS_DATABASE_NUMBER,
)
