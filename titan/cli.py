import asyncio

import typer
from devtools import debug

from .models.keys import KeysTable
from .models.pgsql_manage import (
    AdminsPgSQlManageTable,
    ApisPgSQlManageTable,
    KeysPgSQlManageTable,
    UsersPgSQlManageTable,
)
from .settings.oauth2 import (
    ADMINS_DATABASE_URL,
    ADMINS_TABLE,
    APIS_DATABASE_URL,
    APIS_TABLE,
    KEYS_DATABASE_URL,
    KEYS_TABLE,
    USERS_DATABASE_URL,
    USERS_TABLE,
)

cli = typer.Typer()


run_until_complete = lambda x: asyncio.get_event_loop().run_until_complete(x)


@cli.command("new-users-table")
def new_users_table(users_table: str = USERS_TABLE):
    pgmanage = UsersPgSQlManageTable(USERS_DATABASE_URL, users_table)
    asyncio.get_event_loop().run_until_complete(pgmanage.create_table())


@cli.command("new-admins-table")
def new_admins_table(admins_table: str = ADMINS_TABLE):
    pgmanage = AdminsPgSQlManageTable(ADMINS_DATABASE_URL, admins_table)
    run_until_complete(pgmanage.create_table())


@cli.command("new-keys-table")
def new_keys_table(keys_table: str = KEYS_TABLE, users_table: str = USERS_TABLE):
    pgmanage = KeysPgSQlManageTable(KEYS_DATABASE_URL, keys_table, users_table)
    asyncio.get_event_loop().run_until_complete(pgmanage.create_table())


@cli.command("new-apis-table")
def new_apis_table(
    apis_table: str = APIS_TABLE,
    users_table: str = USERS_TABLE,
    keys_table: str = KEYS_TABLE,
):
    pgmanage = ApisPgSQlManageTable(APIS_DATABASE_URL, apis_table, users_table, keys_table)
    run_until_complete(pgmanage.create_table())


@cli.command("schema")
def print_table_schema(table: str = typer.Argument(..., help="must be one of [users, admins, keys, apis]")):
    table = table.strip().lower()
    pgmanage = None

    if table == "users":
        pgmanage = UsersPgSQlManageTable(USERS_DATABASE_URL, USERS_TABLE)
    if table == "admins":
        pgmanage = AdminsPgSQlManageTable(ADMINS_DATABASE_URL, ADMINS_TABLE)
    if table == "keys":
        pgmanage = KeysPgSQlManageTable(KEYS_DATABASE_URL, KEYS_TABLE, USERS_TABLE)
    if table == "apis":
        pgmanage = ApisPgSQlManageTable(APIS_DATABASE_URL, APIS_TABLE, USERS_TABLE, KEYS_TABLE)

    if pgmanage is None:
        typer.echo(message="table must be one of [users, admins, keys, apis]", err=True)
        exit(1)

    print(pgmanage.str_schema())


@cli.command("new-admin")
def new_admin(email: str, username: str, password: str, scope: str, disabled: bool = False, table: str = ADMINS_TABLE):
    pgmanage = AdminsPgSQlManageTable(ADMINS_DATABASE_URL, table)
    values = {
        "email": email,
        "username": username,
        "password": password,
        "scope": scope,
        "disabled": disabled,
    }
    run_until_complete(pgmanage.insert(values=values))


def coro(f):
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.get_event_loop().run_until_complete(f(*args, **kwargs))

    return wrapper


@cli.command("new-key")
@coro
async def new_key(
    userid: str,
    description: str = "adding test key",
    database_url: str = KEYS_DATABASE_URL,
    keys_table: str = KEYS_TABLE,
    users_table: str = USERS_TABLE,
):
    pg = KeysTable(database_url, keys_table, users_table)
    await pg.connect()
    val = await pg.create(userid, description)
    await pg.disconnect()
    debug(val)


@cli.command("disable-key")
@coro
async def disable_key(
    userid: str,
    keyid: str,
    database_url: str = KEYS_DATABASE_URL,
    keys_table: str = KEYS_TABLE,
    users_table: str = USERS_TABLE,
):
    pg = KeysTable(database_url, keys_table, users_table)
    await pg.connect()
    await pg.disable(userid=userid, keyid=keyid)
    await pg.disconnect()


@cli.command("delete-key")
@coro
async def delete_key(
    userid: str,
    keyid: str,
    database_url: str = KEYS_DATABASE_URL,
    keys_table: str = KEYS_TABLE,
    users_table: str = USERS_TABLE,
):
    pg = KeysTable(database_url, keys_table, users_table)
    await pg.connect()
    await pg.delete(userid=userid, keyid=keyid)
    await pg.disconnect()


if __name__ == "__main__":
    cli()
