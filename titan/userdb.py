from .accounts.user import UserDB
from .settings import USERS_DB_URL, USERS_TABLE_NAME

user_db = UserDB(db_url=USERS_DB_URL, table_name=USERS_TABLE_NAME)
