import typer
from databases import Database
from devtools import debug

from .models.internal import AdminsTableInternal, APIsTableInternal, UsersTableInternal
from .models.manage import AdminsTableManage, APIsTableManage, UsersTableManage
from .models.public import AdminsTable, APIsTable, UsersTable
from .settings.oauth2 import TEST_ADMINS_TABLE, TEST_APIS_TABLE, TEST_PGSQL_URL, TEST_USERS_TABLE
from .utils import coro

cli = typer.Typer()

TEST_DATABSE = Database(TEST_PGSQL_URL)


def setup_wrapper(f):
    from functools import wraps
    from inspect import iscoroutinefunction

    assert iscoroutinefunction(f), f"Expected async def func: ({f})"

    @wraps(f)
    @coro
    async def wrapper(*args, **kwargs):
        await TEST_DATABSE.connect()
        result = await f(*args, **kwargs)
        await TEST_DATABSE.disconnect()
        return result

    return wrapper


users_db = UsersTable(TEST_DATABSE, TEST_USERS_TABLE)
users_db_internal = UsersTableInternal(TEST_DATABSE, TEST_USERS_TABLE)
users_db_manage = UsersTableManage(TEST_DATABSE, TEST_USERS_TABLE)

admins_db = AdminsTable(TEST_DATABSE, TEST_ADMINS_TABLE)
admins_db_internal = AdminsTableInternal(TEST_DATABSE, TEST_ADMINS_TABLE)
admins_db_manage = AdminsTableManage(TEST_DATABSE, TEST_ADMINS_TABLE)

apis_db = APIsTable(TEST_DATABSE, TEST_APIS_TABLE, TEST_USERS_TABLE)
apis_db_internal = APIsTableInternal(TEST_DATABSE, TEST_APIS_TABLE, TEST_USERS_TABLE)
apis_db_manage = APIsTableManage(TEST_DATABSE, TEST_APIS_TABLE, TEST_USERS_TABLE)


@cli.command("new-users-table")
@setup_wrapper
async def new_users_table():
    await users_db_manage.create_table()


@cli.command("new-admins-table")
@setup_wrapper
async def new_admins_table():
    await admins_db_manage.create_table()


@cli.command("new-apis-table")
@setup_wrapper
async def new_apis_table():
    await apis_db_manage.create_table()


@cli.command("schema")
@setup_wrapper
async def print_table_schema(
    table: str = typer.Argument(..., help="must be one of [users, admins, apis]")
):
    table = table.strip().lower()
    pg = None
    if table == "users":
        pg = users_db_manage
    if table == "admins":
        pg = admins_db_manage
    if table == "apis":
        pg = apis_db_manage
    if pg is None:
        typer.echo(message="table must be one of [users, admins, apis]", err=True)
        exit(1)

    print(await pg.str_schema())


@cli.command("new-admin")
@setup_wrapper
async def create_admin(
    email: str,
    username: str,
    password: str,
    scope: str,
):
    val = await admins_db_internal.create(
        email=email, username=username, password=password, scope=scope
    )
    debug(val)


@cli.command("freeze-admin-username")
@setup_wrapper
async def freeze_admin_username(
    username: str,
    freeze: bool = True,
):
    if freeze:
        val = await admins_db_internal.freeze_username(username=username)
    else:
        val = await admins_db_internal.unfreeze_username(username=username)
    debug(val)


@cli.command("freeze-admin-adminid")
@setup_wrapper
async def freeze_admin_adminid(
    adminid: str,
    freeze: bool = True,
):
    if freeze:
        val = await admins_db_internal.freeze_adminid(adminid=adminid)
    else:
        val = await admins_db_internal.unfreeze_adminid(adminid=adminid)
    debug(val)


@cli.command("create-api")
@setup_wrapper
async def create_api(
    userid: str,
    description: str = "adding test api",
):
    new_api = await apis_db.create(userid, description)
    debug(new_api)
    if new_api:
        api = await apis_db.get(userid=new_api.userid, apislug=new_api.apislug)
        verified = apis_db.verify_client_secret(new_api.client_secret, api.secret_hash)
        debug(verified)


@cli.command("get-api")
@setup_wrapper
async def get_api(
    userid: str,
    apislug: str,
):
    api = await apis_db.get(userid, apislug)
    debug(api)


@cli.command("list-apis")
@setup_wrapper
async def list_apis(
    userid: str,
):
    apis = await apis_db.get_all(userid=userid)
    debug(apis)


@cli.command("disable-api")
@setup_wrapper
async def disable_api(
    userid: str,
    apislug: str,
):
    val = await apis_db.disable(userid=userid, apislug=apislug)
    debug(val)


@cli.command("enable-api")
@setup_wrapper
async def enable_api(
    userid: str,
    apislug: str,
):
    val = await apis_db.enable(userid=userid, apislug=apislug)
    debug(val)


@cli.command("delete-api")
@setup_wrapper
async def delete_api(
    userid: str,
    apislug: str,
):
    val = await apis_db.delete(userid=userid, apislug=apislug)
    debug(val)


@cli.command("newkey-api")
@setup_wrapper
async def key_api(
    userid: str,
    apislug: str,
):
    val = await apis_db.update_secret(userid=userid, apislug=apislug)
    debug(val)


@cli.command("list-apis-internal")
@setup_wrapper
async def list_apis_manage(
    userid: str,
):
    apis = await apis_db_internal.get_all(userid=userid)
    debug(apis)


@cli.command("freeze-api")
@setup_wrapper
async def freeze_api(
    userid: str,
    apislug: str,
    freeze: bool = True,
):
    if freeze:
        val = await apis_db_internal.freeze(userid=userid, apislug=apislug)
    else:
        val = await apis_db_internal.unfreeze(userid=userid, apislug=apislug)
    debug(val)


@cli.command("freeze-user-email")
@setup_wrapper
async def freeze_user_email(
    email: str,
    freeze: bool = True,
):
    if freeze:
        val = await apis_db_internal.freeze_email(email=email)
    else:
        val = await apis_db_internal.unfreeze_email(email=email)
    debug(val)


@cli.command("freeze-user-userid")
@setup_wrapper
async def freeze_user_userid(
    userid: str,
    freeze: bool = True,
):
    if freeze:
        val = await users_db_internal.freeze_userid(userid=userid)
    else:
        val = await users_db_internal.unfreeze_userid(userid=userid)
    debug(val)


if __name__ == "__main__":
    cli()
