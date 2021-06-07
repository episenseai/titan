from typing import Optional

from databases import Database
from pydantic import UUID4

from ..base import PgSQLBase
from ..schema.users import NewUser, UserInDB, users_schema


class UsersTable(PgSQLBase):
    def __init__(self, database: Database, users_table: str):
        super().__init__(database=database, table=users_schema(users_table=users_table))

    async def get(
        self, email: Optional[str] = None, userid: Optional[UUID4] = None
    ) -> Optional[UserInDB]:
        """
        User returned might be `frozen`. One should take this into account at the call site.
        """
        if email:
            query = self.table.select().where(self.table.c.email == email)
        elif userid:
            query = self.table.select().where(self.table.c.userid == userid)
        else:
            # neither email nor userid was provided
            return None
        record = await self.database.fetch_one(query=query)
        if record is None:
            return None
        return UserInDB(**record)

    @staticmethod
    def is_frozen(user: UserInDB) -> bool:
        return user.frozen

    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        return await self.get(email=email)

    async def get_by_userid(self, userid: UUID4) -> Optional[UserInDB]:
        return await self.get(userid=userid)

    async def create(
        self,
        email: str,
        idp: str,
        idp_userid: str,
        idp_username: str,
        scope: str,
        full_name: Optional[str] = None,
        picture: Optional[str] = None,
        email_verified: bool = False,
    ) -> Optional[NewUser]:
        """
        Create a new user with `email` as the primary key.
        """
        value = {
            "email": email,
            "idp": idp,
            "idp_userid": idp_userid,
            "idp_username": idp_username,
            "scope": scope,
            "email_verified": email_verified,
        }
        if full_name:
            value.update(full_name=full_name)
        if picture:
            value.update(picture=picture)

        query = (
            self.table.insert()
            .values(value)
            .returning(
                self.table.c.email,
                self.table.c.userid,
                self.table.c.scope,
                self.table.c.full_name,
                self.table.c.picture,
                self.table.c.email_verified,
            )
        )
        newuser = await self.database.fetch_one(query=query)
        if newuser is None:
            return None
        return NewUser(**newuser)

    async def update(
        self,
        user: UserInDB,
        idp_username: Optional[str] = None,
        full_name: Optional[str] = None,
        picture: Optional[str] = None,
    ) -> bool:
        """
        Update user info only if they have changed and the user if not frozen.
        """
        value = {}

        if idp_username != user.idp_username:
            value.update(idp_username=idp_username)
        if full_name != user.full_name:
            value.update(full_name=full_name)
        if picture != user.picture:
            value.update(picture=picture)

        # none of the values need updating
        if not value:
            return False
        # do not update the users, if frozen
        query = (
            self.table.update()
            .where(self.table.c.userid == user.userid)
            .where(self.table.c.email == user.email)
            .where(self.table.c.frozen == False)  # noqa
            .values(value)
            .returning(self.table.c.userid)
        )
        result = await self.database.fetch_one(query=query)
        if result is None:
            # No matching records found. This could either be due to non-existent
            # userid or the user was frozen.
            return False
        return True
