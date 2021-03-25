import asyncio

import typer

from .models.pgsql_manage import (
    AdminsPgSQlManageTable,
    ApisPgSQlManageTable,
    KeysPgSQlManageTable,
    UsersPgSQlManageTable,
)

cli = typer.Typer()

TEST_PGSQL_DB = "postgresql://localhost/testdb"

TEST_USERS_TABLE = "testusers"
TEST_ADMINS_TABLE = "testadmins"
TEST_KEYS_TABLE = "testkeys"
TEST_APIS_TABLE = "testapis"

run_until_complete = lambda x: asyncio.get_event_loop().run_until_complete(x)


@cli.command("new-users-table")
def new_users_table(table: str = TEST_USERS_TABLE):
    pgadmin = UsersPgSQlManageTable(TEST_PGSQL_DB, table)
    asyncio.get_event_loop().run_until_complete(pgadmin.create_table())


@cli.command("new-admins-table")
def new_admins_table(table: str = TEST_ADMINS_TABLE):
    pgadmin = AdminsPgSQlManageTable(TEST_PGSQL_DB, table)
    run_until_complete(pgadmin.create_table())


@cli.command("new-keys-table")
def new_keys_table(table: str = TEST_KEYS_TABLE, users_table: str = TEST_USERS_TABLE):
    pgadmin = KeysPgSQlManageTable(TEST_PGSQL_DB, table, users_table)
    asyncio.get_event_loop().run_until_complete(pgadmin.create_table())


@cli.command("new-apis-table")
def new_apis_table(
    table: str = TEST_APIS_TABLE,
    users_table: str = TEST_USERS_TABLE,
    keys_table: str = TEST_KEYS_TABLE,
):
    pgadmin = ApisPgSQlManageTable(TEST_PGSQL_DB, table, users_table, keys_table)
    run_until_complete(pgadmin.create_table())


@cli.command("schema")
def print_table_schema(table: str = typer.Argument(..., help="must be one of [users, admins, keys, apis]")):
    table = table.strip().lower()
    pgmanage = None

    if table == "users":
        pgmanage = UsersPgSQlManageTable(TEST_PGSQL_DB, TEST_USERS_TABLE)
    if table == "admins":
        pgmanage = AdminsPgSQlManageTable(TEST_PGSQL_DB, TEST_ADMINS_TABLE)
    if table == "keys":
        pgmanage = KeysPgSQlManageTable(TEST_PGSQL_DB, TEST_KEYS_TABLE, TEST_USERS_TABLE)
    if table == "apis":
        pgmanage = ApisPgSQlManageTable(TEST_PGSQL_DB, TEST_APIS_TABLE, TEST_USERS_TABLE, TEST_KEYS_TABLE)

    if pgmanage is None:
        typer.echo(message="table must be one of [users, admins, keys, apis]", err=True)
        exit(1)

    print(pgmanage.str_schema())


@cli.command("new-admin")
def new_admin(
    email: str, username: str, password: str, scope: str, disabled: bool = False, table: str = TEST_ADMINS_TABLE
):
    pgadmin = AdminsPgSQlManageTable(TEST_PGSQL_DB, table)
    values = {
        "email": email,
        "username": username,
        "password": password,
        "scope": scope,
        "disabled": disabled,
    }
    run_until_complete(pgadmin.insert(values=values))


if __name__ == "__main__":
    cli()
