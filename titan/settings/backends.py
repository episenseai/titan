from ..auth.state import StateTokensDB
from ..models.public.admins import AdminsTable
from ..models.public.users import UsersTable
from .oauth2 import ADMINS_DATABASE_URL, ADMINS_TABLE, USERS_DATABASE_URL, USERS_TABLE

users_db = UsersTable(database_url=USERS_DATABASE_URL, table_name=USERS_TABLE)

admins_db = AdminsTable(database_url=ADMINS_DATABASE_URL, table_name=ADMINS_TABLE)

state_tokens_db = StateTokensDB()
