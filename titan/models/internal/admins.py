from databases import Database

from ..base import PgSQLBase
from ..schema.admins import admins_schema


class AdminsTableInternal(PgSQLBase):
    def __init__(
        self,
        database_url: str,
        admins_table: str,
    ) -> None:
        super().__init__(
            database=Database(database_url),
            table=admins_schema(admins_table=admins_table),
        )

    async def freeze_adminid(self, adminid: str):
        # TODO
        pass

    async def unfreeze_adminid(self, adminid: str):
        # TODO
        pass

    async def freeze_username(self, username: str):
        # TODO
        pass

    async def unfreeze_username(self, username: str):
        # TODO
        pass

    async def freeze_email(self, email: str):
        """
        Freeze all 'username' associated with this email.
        """
        # TODO
        pass

    def unfreeze_email(self, email: str):
        """
        Freeze all 'username' associated with this email.
        """
        # TODO
        pass
