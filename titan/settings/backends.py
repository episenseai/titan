from ..auth.state import StateTokensDB
from ..models.public import AdminsTable, APIsTable, UsersTable
from .oauth2 import ADMINS_DATABASE_URL, ADMINS_TABLE, APIS_DATABASE_URL, APIS_TABLE, USERS_DATABASE_URL, USERS_TABLE

users_db = UsersTable(database_url=USERS_DATABASE_URL, table_name=USERS_TABLE)

admins_db = AdminsTable(database_url=ADMINS_DATABASE_URL, table_name=ADMINS_TABLE)

apis_db = APIsTable(database_url=APIS_DATABASE_URL, apis_table=APIS_TABLE, users_table=USERS_TABLE)

state_tokens_db = StateTokensDB()
