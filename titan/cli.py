import typer
from devtools import debug

from .models.internal import AdminsTableInternal, APIsTableInternal, UsersTableInternal
from .models.manage import AdminsTableManage, APIsTableManage, UsersTableManage
from .models.public import AdminsTable, APIsTable, UsersTable
from .settings.oauth2 import (
    ADMINS_DATABASE_URL,
    ADMINS_TABLE,
    APIS_DATABASE_URL,
    APIS_TABLE,
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


@cli.command("new-apis-table")
@coro
async def new_apis_table(
    apis_table: str = APIS_TABLE,
    users_table: str = USERS_TABLE,
):
    pg = APIsTableManage(APIS_DATABASE_URL, apis_table, users_table)
    async with pg:
        await pg.create_table()


@cli.command("schema")
def print_table_schema(table: str = typer.Argument(..., help="must be one of [users, admins, apis]")):
    table = table.strip().lower()
    pg = None

    if table == "users":
        pg = UsersTableManage(USERS_DATABASE_URL, USERS_TABLE)
    if table == "admins":
        pg = AdminsTableManage(ADMINS_DATABASE_URL, ADMINS_TABLE)
    if table == "apis":
        pg = APIsTableManage(APIS_DATABASE_URL, APIS_TABLE, USERS_TABLE)

    if pg is None:
        typer.echo(message="table must be one of [users, admins, apis]", err=True)
        exit(1)

    print(pg.str_schema())


@cli.command("new-admin")
@coro
async def create_admin(
    email: str,
    username: str,
    password: str,
    scope: str,
    disabled: bool = False,
    database_url: str = ADMINS_DATABASE_URL,
    admins_table: str = ADMINS_TABLE,
):
    pg = AdminsTableInternal(database_url, admins_table)
    values = {
        "email": email,
        "username": username,
        "password": password,
        "scope": scope,
        "disabled": disabled,
    }
    async with pg:
        await pg.insert(values=values)


@cli.command("new-api")
@coro
async def create_api(
    userid: str,
    description: str = "adding test api",
    database_url: str = APIS_DATABASE_URL,
    apis_table: str = APIS_TABLE,
    users_table: str = USERS_TABLE,
):
    pg = APIsTable(database_url, apis_table, users_table)
    async with pg:
        val = await pg.create(userid, description)
        debug(val)


@cli.command("get-api")
@coro
async def get_api(
    userid: str,
    apislug: str,
    database_url: str = APIS_DATABASE_URL,
    apis_table: str = APIS_TABLE,
    users_table: str = USERS_TABLE,
):
    pg = APIsTable(database_url, apis_table, users_table)
    async with pg:
        val = await pg.get(userid, apislug)
        debug(val)


@cli.command("list-apis")
@coro
async def list_apis(
    userid: str,
    database_url: str = APIS_DATABASE_URL,
    apis_table: str = APIS_TABLE,
    users_table: str = USERS_TABLE,
):
    pg = APIsTable(database_url, apis_table, users_table)
    async with pg:
        apis = await pg.get_all(userid=userid)
        debug(apis)


@cli.command("disable-api")
@coro
async def disable_api(
    userid: str,
    apislug: str,
    database_url: str = APIS_DATABASE_URL,
    apis_table: str = APIS_TABLE,
    users_table: str = USERS_TABLE,
):
    pg = APIsTable(database_url, apis_table, users_table)
    async with pg:
        val = await pg.disable(userid=userid, apislug=apislug)
        debug(val)


@cli.command("enable-api")
@coro
async def enable_api(
    userid: str,
    apislug: str,
    database_url: str = APIS_DATABASE_URL,
    apis_table: str = APIS_TABLE,
    users_table: str = USERS_TABLE,
):
    pg = APIsTable(database_url, apis_table, users_table)
    async with pg:
        val = await pg.enable(userid=userid, apislug=apislug)
        debug(val)


@cli.command("delete-api")
@coro
async def delete_api(
    userid: str,
    apislug: str,
    database_url: str = APIS_DATABASE_URL,
    apis_table: str = APIS_TABLE,
    users_table: str = USERS_TABLE,
):
    pg = APIsTable(database_url, apis_table, users_table)
    async with pg:
        val = await pg.delete(userid=userid, apislug=apislug)
        debug(val)


@cli.command("update-api")
@coro
async def update_api(
    userid: str,
    apislug: str,
    database_url: str = APIS_DATABASE_URL,
    apis_table: str = APIS_TABLE,
    users_table: str = USERS_TABLE,
):
    pg = APIsTable(database_url, apis_table, users_table)
    async with pg:
        val = await pg.update_secret(userid=userid, apislug=apislug)
        debug(val)


@cli.command("list-apis-internal")
@coro
async def list_apis_manage(
    userid: str,
    database_url: str = APIS_DATABASE_URL,
    apis_table: str = APIS_TABLE,
    users_table: str = USERS_TABLE,
):
    pg = APIsTableInternal(database_url, apis_table, users_table)
    async with pg:
        apis = await pg.get_all(userid=userid)
        debug(apis)


@cli.command("freeze-api")
@coro
async def freeze_api(
    userid: str,
    apislug: str,
    freeze: bool = True,
    database_url: str = APIS_DATABASE_URL,
    apis_table: str = APIS_TABLE,
    users_table: str = USERS_TABLE,
):
    pg = APIsTableInternal(database_url, apis_table, users_table)
    async with pg:
        if freeze:
            val = await pg.freeze(userid=userid, apislug=apislug)
        else:
            val = await pg.unfreeze(userid=userid, apislug=apislug)
        debug(val)


@cli.command("freeze-user-email")
@coro
async def freeze_user_email(
    email: str,
    freeze: bool = True,
    database_url=USERS_DATABASE_URL,
    users_table: str = USERS_TABLE,
):
    pg = UsersTableInternal(database_url, users_table)

    async with pg:
        if freeze:
            val = await pg.freeze_email(email=email)
        else:
            val = await pg.unfreeze_email(email=email)
        debug(val)


@cli.command("freeze-user-userid")
@coro
async def freeze_user_userid(
    userid: str,
    freeze: bool = True,
    database_url=USERS_DATABASE_URL,
    users_table: str = USERS_TABLE,
):
    pg = UsersTableInternal(database_url, users_table)

    async with pg:
        if freeze:
            val = await pg.freeze_userid(userid=userid)
        else:
            val = await pg.unfreeze_userid(userid=userid)
        debug(val)


if __name__ == "__main__":
    cli()
