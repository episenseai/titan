import typer
from databases import Database

from .models.internal import AdminsTableInternal, APIsTableInternal, UsersTableInternal
from .models.manage import AdminsTableManage, APIsTableManage, UsersTableManage
from .models.public import AdminsTable, APIsTable, UsersTable
from .settings.env import ADMINS_TABLE, APIS_TABLE, USERS_TABLE, env
from .utils import coro

cli = typer.Typer()

postgres_database = Database(
    url=env().postgres_url,
    user=env().POSTGRESQL_USER,
    password=env().POSTGRESQL_PASSWORD.get_secret_value(),
)


def setup_wrapper(f):
    from functools import wraps
    from inspect import iscoroutinefunction

    assert iscoroutinefunction(f), f"Expected async def func: ({f})"

    @wraps(f)
    @coro
    async def wrapper(*args, **kwargs):
        await postgres_database.connect()
        result = await f(*args, **kwargs)
        await postgres_database.disconnect()
        return result

    return wrapper


users_db = UsersTable(postgres_database, USERS_TABLE)
users_db_internal = UsersTableInternal(postgres_database, USERS_TABLE)
users_db_manage = UsersTableManage(postgres_database, USERS_TABLE)

admins_db = AdminsTable(postgres_database, ADMINS_TABLE)
admins_db_internal = AdminsTableInternal(postgres_database, ADMINS_TABLE)
admins_db_manage = AdminsTableManage(postgres_database, ADMINS_TABLE)

apis_db = APIsTable(postgres_database, APIS_TABLE, USERS_TABLE)
apis_db_internal = APIsTableInternal(postgres_database, APIS_TABLE, USERS_TABLE)
apis_db_manage = APIsTableManage(postgres_database, APIS_TABLE, USERS_TABLE)


@cli.command("create-new-tables", short_help="Creat new tables for users, admins and apis.")
@setup_wrapper
async def create_new_tables():
    print("** Trying to create new (users) table for testing.")
    await users_db_manage.create_table()
    print("** Trying to create new (admins) table for testing.")
    await admins_db_manage.create_table()
    print("** Trying to create new (apis) table for testing.")
    await apis_db_manage.create_table()


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
    print(val)


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
    print(val)


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
    print(val)


@cli.command("create-api")
@setup_wrapper
async def create_api(
    userid: str,
    description: str = "adding test api",
):
    new_api = await apis_db.create(userid, description)
    print(new_api)
    if new_api:
        api = await apis_db.get(userid=new_api.userid, apislug=new_api.apislug)
        if api is None:
            print("Could not get api after creation")
        else:
            verified = apis_db.verify_client_secret(new_api.client_secret, api.secret_hash)
            print(verified)


@cli.command("get-api")
@setup_wrapper
async def get_api(
    userid: str,
    apislug: str,
):
    api = await apis_db.get(userid, apislug)
    print(api)


@cli.command("list-apis")
@setup_wrapper
async def list_apis(
    userid: str,
):
    apis = await apis_db.get_all(userid=userid)
    print(apis)


@cli.command("disable-api")
@setup_wrapper
async def disable_api(
    userid: str,
    apislug: str,
):
    val = await apis_db.disable(userid=userid, apislug=apislug)
    print(val)


@cli.command("enable-api")
@setup_wrapper
async def enable_api(
    userid: str,
    apislug: str,
):
    val = await apis_db.enable(userid=userid, apislug=apislug)
    print(val)


@cli.command("delete-api")
@setup_wrapper
async def delete_api(
    userid: str,
    apislug: str,
):
    val = await apis_db.delete(userid=userid, apislug=apislug)
    print(val)


@cli.command("newkey-api")
@setup_wrapper
async def key_api(
    userid: str,
    apislug: str,
):
    val = await apis_db.update_secret(userid=userid, apislug=apislug)
    print(val)


@cli.command("list-apis-internal")
@setup_wrapper
async def list_apis_manage(
    userid: str,
):
    apis = await apis_db_internal.get_all(userid=userid)
    print(apis)


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
    print(val)


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
    print(val)


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
    print(val)


if __name__ == "__main__":
    cli()
