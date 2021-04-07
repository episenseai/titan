from databases import Database

from ..auth.state import StateTokensDB
from ..models.internal import AdminsTableInternal, APIsTableInternal, UsersTableInternal
from ..models.manage import AdminsTableManage, APIsTableManage, UsersTableManage
from ..models.public import AdminsTable, APIsTable, UsersTable
from .oauth2 import TEST_ADMINS_TABLE, TEST_APIS_TABLE, TEST_PGSQL_URL, TEST_USERS_TABLE

TEST_DATABSE = Database(TEST_PGSQL_URL)

users_db = UsersTable(TEST_DATABSE, TEST_USERS_TABLE)
users_db_internal = UsersTableInternal(TEST_DATABSE, TEST_USERS_TABLE)

admins_db = AdminsTable(TEST_DATABSE, TEST_ADMINS_TABLE)
admins_db_internal = AdminsTableInternal(TEST_DATABSE, TEST_ADMINS_TABLE)

apis_db = APIsTable(TEST_DATABSE, TEST_APIS_TABLE, TEST_USERS_TABLE)
apis_db_internal = APIsTableInternal(TEST_DATABSE, TEST_APIS_TABLE, TEST_USERS_TABLE)


async def check_table_existence():
    dbs = []

    dbs.append(UsersTableManage(TEST_DATABSE, TEST_USERS_TABLE))
    dbs.append(AdminsTableManage(TEST_DATABSE, TEST_ADMINS_TABLE))
    dbs.append(APIsTableManage(TEST_DATABSE, TEST_APIS_TABLE, TEST_USERS_TABLE))

    for db in dbs:
        exists = await db.exists_table_in_db()
        if not exists:
            raise RuntimeError(f"Table missing: (database={db.database.url}, table={db.table.name})")


state_tokens_db = StateTokensDB()
