import asyncio

import typer
from databases import Database

from .accounts.schema import create_users_table
from .admin.schema import admins_schema, create_admins_table

cli = typer.Typer()

# Only use it for testing and developement.
testdb = Database("postgresql://localhost/testdb")


@cli.command("new-users-table")
def new_users_table_demo(table_name: str):
    asyncio.get_event_loop().run_until_complete(
        create_users_table(
            database=testdb,
            table_name=table_name,
        )
    )


@cli.command("new-admins-table")
def new_admins_table_demo(table_name: str):
    asyncio.get_event_loop().run_until_complete(
        create_admins_table(
            database=testdb,
            table_name=table_name,
        )
    )


async def new_user_demo(table_name: str, email: str, username: str, password: str, scope: str, disabled: bool = False):
    admins_table = admins_schema(table_name=table_name)

    query = admins_table.insert()
    values = {
        "email": email,
        "username": username,
        "password": password,
        "scope": scope,
        "disabled": disabled,
    }

    await testdb.connect()
    await testdb.execute(query=query, values=values)
    await testdb.disconnect()


@cli.command("new-admin")
def new_admin_demo(table_name: str, email: str, username: str, password: str, scope: str, disabled: bool = False):
    asyncio.get_event_loop().run_until_complete(
        new_user_demo(
            table_name=table_name,
            email=email,
            username=username,
            password=password,
            scope=scope,
            disabled=disabled,
        )
    )


if __name__ == "__main__":
    cli()
