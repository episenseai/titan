from typing import Optional

from databases import Database
from pydantic import UUID4

from ..base import PgSQLBase
from ..schema.users import NewUser, UserInDB, users_schema


class UsersTable(PgSQLBase):
    def __init__(self, database_url: str, table_name: str):
        super().__init__(Database(database_url), users_schema(users_table=table_name))

    async def get(self, email: Optional[str] = None, userid: Optional[UUID4] = None) -> Optional[UserInDB]:
        """
        User might be frozen might be user. Take into account the frozen attribute
        while making decisions.
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
        email: str
        full_name: Optional[str] = None
        picture: Optional[str] = None
        idp: IdentityProvider
        idp_userid: str
        idp_username: Optional[str] = None
        provider_creds: Optional[OAuth2AuthentcatedCreds] = None
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

    async def update(self, user: UserInDB):
        pass
