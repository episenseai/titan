import typer
from devtools import debug

from .models.internal import AdminsTableInternal, ApisTableInternal, KeysTableInternal, UsersTableInternal
from .models.manage import AdminsTableManage, ApisTableManage, KeysTableManage, UsersTableManage
from .models.public import AdminsTable, ApisTable, KeysTable, UsersTable
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
from .utils import coro

cli = typer.Typer()


@cli.command("new-users-table")
@coro
async def new_users_table(users_table: str = USERS_TABLE):
    pg = UsersTableManage(USERS_DATABASE_URL, users_table)
    async with pg:
        await pg.create_table()


@cli.command("new-admins-table")
@coro
async def new_admins_table(admins_table: str = ADMINS_TABLE):
    pg = AdminsTableManage(ADMINS_DATABASE_URL, admins_table)
    async with pg:
        await pg.create_table()


@cli.command("new-keys-table")
@coro
async def new_keys_table(keys_table: str = KEYS_TABLE, users_table: str = USERS_TABLE):
    pg = KeysTableManage(KEYS_DATABASE_URL, keys_table, users_table)
    async with pg:
        await pg.create_table()


@cli.command("new-apis-table")
@coro
async def new_apis_table(
    apis_table: str = APIS_TABLE,
    users_table: str = USERS_TABLE,
    keys_table: str = KEYS_TABLE,
):
    pg = ApisTableManage(APIS_DATABASE_URL, apis_table, users_table, keys_table)
    async with pg:
        await pg.create_table()


@cli.command("schema")
def print_table_schema(table: str = typer.Argument(..., help="must be one of [users, admins, keys, apis]")):
    table = table.strip().lower()
    pg = None

    if table == "users":
        pg = UsersTableManage(USERS_DATABASE_URL, USERS_TABLE)
    if table == "admins":
        pg = AdminsTableManage(ADMINS_DATABASE_URL, ADMINS_TABLE)
    if table == "keys":
        pg = KeysTableManage(KEYS_DATABASE_URL, KEYS_TABLE, USERS_TABLE)
    if table == "apis":
        pg = ApisTableManage(APIS_DATABASE_URL, APIS_TABLE, USERS_TABLE, KEYS_TABLE)

    if pg is None:
        typer.echo(message="table must be one of [users, admins, keys, apis]", err=True)
        exit(1)

    print(pg.str_schema())


@cli.command("new-admin")
@coro
async def create_admin(
    email: str, username: str, password: str, scope: str, disabled: bool = False, table: str = ADMINS_TABLE
):
    pg = AdminsTableInternal(ADMINS_DATABASE_URL, table)
    values = {
        "email": email,
        "username": username,
        "password": password,
        "scope": scope,
        "disabled": disabled,
    }
    async with pg:
        await pg.insert(values=values)


@cli.command("new-key")
@coro
async def create_key(
    userid: str,
    description: str = "adding test key",
    database_url: str = KEYS_DATABASE_URL,
    keys_table: str = KEYS_TABLE,
    users_table: str = USERS_TABLE,
):
    pg = KeysTable(database_url, keys_table, users_table)
    async with pg:
        val = await pg.create(userid, description)
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
    async with pg:
        await pg.disable(userid=userid, keyid=keyid)


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
    async with pg:
        await pg.delete(userid=userid, keyid=keyid)


@cli.command("list-keys")
@coro
async def list_keys(
    userid: str,
    database_url: str = KEYS_DATABASE_URL,
    keys_table: str = KEYS_TABLE,
    users_table: str = USERS_TABLE,
):
    pg = KeysTable(database_url, keys_table, users_table)
    async with pg:
        keys = await pg.get_all(userid=userid)
        debug(keys)


@cli.command("list-keys-manage")
@coro
async def list_keys_manage(
    userid: str,
    database_url: str = KEYS_DATABASE_URL,
    keys_table: str = KEYS_TABLE,
    users_table: str = USERS_TABLE,
):
    pg = KeysTableInternal(database_url, keys_table, users_table)
    async with pg:
        keys = await pg.get_all(userid=userid)
        debug(keys)


@cli.command("freeze-key")
@coro
async def freeze_key(
    userid: str,
    keyid: str,
    freeze: bool = True,
    database_url: str = KEYS_DATABASE_URL,
    keys_table: str = KEYS_TABLE,
    users_table: str = USERS_TABLE,
):
    pg = KeysTableInternal(database_url, keys_table, users_table)
    async with pg:
        if freeze:
            val = await pg.freeze(userid=userid, keyid=keyid)
        else:
            val = await pg.unfreeze(userid=userid, keyid=keyid)
        debug(val)


if __name__ == "__main__":
    cli()
