import secrets
from enum import Enum, unique
from typing import ClassVar, Optional

from asyncpg.exceptions import ForeignKeyViolationError, UniqueViolationError
from databases import Database
from passlib.context import CryptContext
from pydantic import UUID4

from ..base import PgSQLBase
from ..schema.apis import AllAPIsInDB, APIInDB, NewAPI, apis_schema


@unique
class APIState(str, Enum):
    FORZEN = "forzen"
    DISABLED = "disabled"
    ENABLED = "enabled"
    DELETED = "deleted"
    UNKNOWN = "unknown"


class APIsTable(PgSQLBase):
    # 'bcrypt' truncates ones larger than 72 bytes. truncate_error=True will
    # raise a PasswordTruncateError.
    pwd_context: ClassVar[CryptContext] = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        truncate_error=True,
    )

    def __init__(self, database: Database, apis_table: str, users_table: str):
        super().__init__(
            database=database,
            table=apis_schema(apis_table=apis_table, users_table=users_table),
        )

    def gen_apislug(self) -> str:
        return secrets.token_urlsafe(nbytes=32)

    def generate_client_secret(self, nbytes: int = 48) -> Optional[tuple[str, str]]:
        """
        48 bytes = 384 bits of randomness should suffice for now. 'client_secret'
        is base64 encoded so each byte results in approximately 1.3 characters.
        Resulting secret is thus 64 characters long which is less than 72, maximum
        password len supported by 'bcrypt` before truncation.
        """
        try:
            # send back with reponse to the create api call. Ask the client
            # to save the client_secret and do not store this on the server.
            client_secret = secrets.token_urlsafe(nbytes)
            # save the hash of the client_secret for verification.
            secret_hash = self.pwd_context.hash(client_secret)
            return (client_secret, secret_hash)
        except Exception as exc:
            print(f"coud not generate client_secret: {exc}")
            return None

    def verify_client_secret(self, client_secret: str, secret_hash: str) -> bool:
        try:
            return self.pwd_context.verify(client_secret, secret_hash)
        except Exception as exc:
            print(f"could bot verify client_secret: {exc}")
            return False

    async def get(self, userid: UUID4, apislug: str) -> Optional[APIInDB]:
        """
        If the API was deleted by the user, do not return in any subsequent queries.
        """
        query = self.table.select().where(self.table.c.userid == userid).where(self.table.c.apislug == apislug)
        record = await self.database.fetch_one(query=query)
        if record is None:
            return None
        api = APIInDB(**record)
        if api.deleted:
            # api has been deleted
            return None
        return api

    async def get_all(self, userid: UUID4) -> AllAPIsInDB:
        """
        If the API was deleted by the user, do not return in any subsequent queries.
        """
        query = self.table.select().where(self.table.c.userid == userid)
        records = await self.database.fetch_all(query=query)
        if not records:
            return AllAPIsInDB(apis=[])
        return AllAPIsInDB(apis=({**record} for record in records if record.get("deleted") is False))

    async def create(self, userid: UUID4, description: str) -> Optional[NewAPI]:
        """
        Generates a client_secret and associates with the API. Return the client_secret
        and save only the hash of it to for verification.
        """
        res = self.generate_client_secret()
        if res is None:
            # error happened while generating client_secret
            return None

        client_secret, secret_hash = res

        # trying a few times to get a unique apislug, in case the it already
        # exists in database.
        for _ in range(4):
            try:
                apislug = self.gen_apislug()
                value = {
                    "apislug": apislug,
                    "userid": userid,
                    "secret_hash": secret_hash,
                    "description": description,
                }
                query = (
                    self.table.insert()
                    .values(value)
                    .returning(
                        self.table.c.apislug,
                        self.table.c.userid,
                        self.table.c.description,
                    )
                )
                newapi = await self.database.fetch_one(query=query)
                return NewAPI(**newapi, client_secret=client_secret)
            except UniqueViolationError:
                print("generated apislug exists in database. trying again...")
                pass
            except ForeignKeyViolationError as exc:
                print(f"could not create api: {exc}")
                return None
        # Could not generate a unique apislug after a few tries. Ideally the chances
        # of this happening is negligible.
        return None

    async def update_secret(self, userid: UUID4, apislug: str) -> Optional[str]:
        """
        Regenerate a fresh client_secret for the API and invalidate the previous one.
        This can be used by the user in case their client_secret is compromised.

        If the API is frozen the updating is not allowed.
        """
        res = self.generate_client_secret()
        if res is None:
            # error happened while generating client_secret
            return None

        client_secret, secret_hash = res

        # do not update if the API is frozen
        query = (
            self.table.update()
            .where(self.table.c.userid == userid)
            .where(self.table.c.apislug == apislug)
            .where(self.table.c.frozen == False)  # noqa
            .values({"secret_hash": secret_hash})
            .returning(self.table.c.apislug)
        )
        result = await self.database.fetch_one(query=query)
        if result is None:
            # No matching records found. This could either be due to non-existent
            # userid/apislug or the api was frozen.
            return None
        # this equality test is gratuitous
        if apislug == result.get("apislug"):
            return client_secret
        # this should never happen
        return None

    async def toggle(self, userid: UUID4, apislug: str, disabled: bool) -> Optional[APIState]:
        async with self.database.transaction():
            api = await self.get(userid, apislug)
            if api is None:
                # No matching api found
                return None
            if api.frozen:
                # API was frozen by admin
                return APIState.FORZEN
            if disabled and api.disabled:
                # API is already disabled
                return APIState.DISABLED
            if (not disabled) and (not api.frozen):
                # API is already enabled
                return APIState.ENABLED

            query = (
                self.table.update()
                .where(self.table.c.userid == userid)
                .where(self.table.c.apislug == apislug)
                .values({"disabled": disabled})
                .returning(self.table.c.disabled)
            )
            result = await self.database.fetch_one(query=query)
            if result is None:
                # this should never happen as we have already checked the existence
                # of api and we are doing a transaction.
                return APIState.UNKNOWN
            if disabled and result.get("disabled"):
                return APIState.DISABLED
            if (not disabled) and (not result.get("disabled")):
                return APIState.ENABLED
            else:
                # this should never happen
                return APIState.UNKNOWN

    async def disable(self, userid: UUID4, apislug: str) -> Optional[APIState]:
        """
        Temporarily disables the API.
        """
        return await self.toggle(userid, apislug, disabled=True)

    async def enable(self, userid: UUID4, apislug: str) -> Optional[APIState]:
        """
        Re-enable the API
        """
        return await self.toggle(userid, apislug, disabled=False)

    async def delete(self, userid: UUID4, apislug: str) -> Optional[APIState]:
        """
        After the deletion API will not show up any query by the user. Deleted API can
        still be accessed through admin interface.
        """
        async with self.database.transaction():
            api = await self.get(userid, apislug)
            if api is None:
                # No matching API found
                return None
            if api.frozen:
                # API was frozen by admin, can not delete it.
                return APIState.FORZEN

            query = (
                self.table.update()
                .where(self.table.c.userid == userid)
                .where(self.table.c.apislug == apislug)
                .values({"deleted": True})
                .returning(self.table.c.deleted)
            )
            result = await self.database.fetch_one(query=query)
            if result is None:
                # this should never happen as we have already checked the existence
                # of api and we are doing a transaction.

                return APIState.UNKNOWN

            if result.get("deleted") is True:
                return APIState.DELETED
            # thi should never happen
            return APIState.UNKNOWN
