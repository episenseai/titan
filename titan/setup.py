import typer
import asyncio
from databases import Database
from .admin.schema import create_admins_table
from .accounts.schema import create_users_table

cli = typer.Typer()


@cli.command("new-admins-table")
def new_admins_table_testdb(table_name: str):
    """
    Only use it for testing and developement.
    """
    database = Database("postgresql://localhost/testdb")
    asyncio.get_event_loop().run_until_complete(
        create_admins_table(
            database=database,
            table_name=table_name,
        )
    )


@cli.command("new-users-table")
def new_users_table_testdb(table_name: str):
    """
    Only use it for testing and developement.
    """
    database = Database("postgresql://localhost/testdb")
    asyncio.get_event_loop().run_until_complete(
        create_users_table(
            database=database,
            table_name=table_name,
        )
    )


if __name__ == "__main__":
    cli()
