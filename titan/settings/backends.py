from asyncpg.exceptions import (
    CannotConnectNowError,
    ClientCannotConnectError,
    ConnectionDoesNotExistError,
    ConnectionFailureError,
    ConnectionRejectionError,
    InvalidCatalogNameError,
)
from databases import Database

from ..auth.state import StateTokensDB
from ..logger import logger
from ..models.internal import AdminsTableInternal, APIsTableInternal, UsersTableInternal
from ..models.manage import AdminsTableManage, APIsTableManage, UsersTableManage
from ..models.public import AdminsTable, APIsTable, UsersTable
from .env import ADMINS_TABLE, APIS_TABLE, USERS_TABLE, env
from .idp import google_auth_client

postgres_database = Database(
    url=env().postgres_url,
    user=env().POSTGRESQL_USER,
    password=env().postgres_pasword,
)

users_db = UsersTable(postgres_database, USERS_TABLE)
users_db_internal = UsersTableInternal(postgres_database, USERS_TABLE)

admins_db = AdminsTable(postgres_database, ADMINS_TABLE)
admins_db_internal = AdminsTableInternal(postgres_database, ADMINS_TABLE)

apis_db = APIsTable(postgres_database, APIS_TABLE, USERS_TABLE)
apis_db_internal = APIsTableInternal(postgres_database, APIS_TABLE, USERS_TABLE)


async def postgres_connect(retries: int = 4, backoff_seconds: int = 5):
    for x in range(retries):
        try:
            await postgres_database.connect()
            return True
        except (
            ConnectionRefusedError,
            CannotConnectNowError,
            ClientCannotConnectError,
            ConnectionDoesNotExistError,
            ConnectionFailureError,
            ConnectionRejectionError,
        ) as ex:
            if x < 3:
                logger.warn(f"Could not connect to {env().postgres_url}")
                logger.info(f"Retry connecting to {env().postgres_url} in {backoff_seconds}sec")
                import time

                time.sleep(backoff_seconds)
                # linear backoff
                backoff_seconds = backoff_seconds + 3
                continue
            logger.exception(f"Failed connecting to {env().postgres_url} ({x+1} attempts)")
            return False
        except InvalidCatalogNameError as ex:
            logger.error(
                f"Database '{env().POSTGRESQL_DATABASE}' does not exist ({env().postgres_url})"
            )
            return False


async def check_table_existence():
    dbs = []

    dbs.append(UsersTableManage(postgres_database, USERS_TABLE))
    dbs.append(AdminsTableManage(postgres_database, ADMINS_TABLE))
    dbs.append(APIsTableManage(postgres_database, APIS_TABLE, USERS_TABLE))

    for db in dbs:
        exists = await db.exists_table_in_db()
        if not exists:
            logger.error(f"Table missing: (database={db.database.url}, table={db.table.name})")
            return False
    return True


async def initialize_JWKS_keys():
    """
    Run this in production to aovid fetching keys over and over again
    """
    if google_auth_client.jwks_uri is None:
        logger.error("Google missing JWKS uri: needed for GoogleAuthClient")
        exit(1)
    try:
        await google_auth_client.update_jwks_keys()
    except Exception:
        logger.exception("Could not download JWKS keys from Google")
        exit(1)


state_tokens_db = StateTokensDB(
    redis_host=env().REDIS_HOST,
    redis_port=env().REDIS_PORT,
    redis_password=env().redis_pasword,
    redis_db=env().REDIS_DATABASE_NUMBER,
)
