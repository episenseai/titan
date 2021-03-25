from ..auth.state import StateTokensDB
from ..models.admins import AdminsTable
from ..models.users import UsersTable
from .oauth2 import ADMINS_DB_URL, ADMINS_TABLE_NAME, USERS_DB_URL, USERS_TABLE_NAME

users_db = UsersTable(database_url=USERS_DB_URL, table_name=USERS_TABLE_NAME)

admins_db = AdminsTable(database_url=ADMINS_DB_URL, table_name=ADMINS_TABLE_NAME)

state_tokens_db = StateTokensDB()
