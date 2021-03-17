from .settings import ADMINS_DB_URL, ADMINS_TABLE_NAME
from .admin.user import AdminDB


admin_db = AdminDB(db_url=ADMINS_DB_URL, table_name=ADMINS_TABLE_NAME)
