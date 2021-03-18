from typing import Optional

from databases import Database

from ..exceptions import DatabaseUserFetchError
from ..oauth2.models import OAuth2AuthentcatedUser
from .schema import users_schema, UserInDB


class UserDB:
    def __init__(self, db_url: str, table_name: str):
        self.database = Database(db_url)
        self.table = users_schema(table_name=table_name)

    async def connect(self):
        await self.database.connect()

    async def disconnect(self):
        await self.database.disconnect()

    async def get_user(self, email: str = None, guid: str = None) -> Optional[UserInDB]:
        empty_query = True
        # select query
        query = self.table.select()
        # select query by email
        if isinstance(email, str):
            query = query.where(self.table.columns.email == email)
            empty_query = False
        # select query by guid
        if isinstance(guid, str):
            query = query.where(self.table.columns.guid == guid)
            empty_query = False
        if empty_query:
            return None

        # Returns None if the user is not in DB
        user = await self.database.fetch_one(query=query)

        if user is not None:
            try:
                return UserInDB(**user)
            except Exception as exc:
                print(f"Error {user=} for {email=} {guid=}")
                raise DatabaseUserFetchError from exc
        return None

    async def create_user(self, user: OAuth2AuthentcatedUser, disabled: bool = False, email_verified: bool = False):
        basic_scope = "episense:demo"
        query = self.table.insert()
        values = user.dict(
            include={"email", "full_name", "picture", "idp", "idp_guid", "idp_username"},
        )
        values.update(
            {
                "disabled": disabled,
                "email_verified": email_verified,
                "scope": basic_scope,
            }
        )
        await self.database.execute(query=query, values=values)

    async def try_update_user(self, user: UserInDB):
        pass
