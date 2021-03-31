import secrets
from typing import ClassVar, Optional

from databases import Database
from passlib.context import CryptContext
from pydantic import UUID4

from ..base import PgSQLBase
from ..schema.keys import AllKeysInDB, KeyInDB, NewKey, keys_schema


class KeysTable(PgSQLBase):
    # 'bcrypt' truncates ones larger than 72 bytes. truncate_error=True will
    # raise a PasswordTruncateError.
    pwd_context: ClassVar[CryptContext] = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
        truncate_error=True,
    )

    def __init__(self, database_url: str, keys_table: str, users_table: str) -> None:
        super().__init__(
            Database(database_url),
            keys_schema(keys_table=keys_table, users_table=users_table),
        )

    def generate_client_secret(self, nbytes: int = 48) -> str:
        """
        48 bytes = 384 bits of randomness should suffice for now. 'client_secret'
        is base64 encoded so each byte results in approximately 1.3 characters.
        Resulting secret is thus 64 characters long which is less than 72, maximum
        password len supported by 'bcrypt` before truncation.
        """
        # send back with reponse to the create key api call. Ask the client
        # to save the client_secret and do not store this on the server.
        client_secret = secrets.token_urlsafe(nbytes)
        print(len(client_secret))
        # save the hash of the key for verifying the client_secret/key later.
        secret_hash = self.pwd_context.hash(client_secret)
        return (client_secret, secret_hash)

    async def get(self, userid: UUID4, keyid: UUID4) -> Optional[KeyInDB]:
        """
        If the key was deleted by the user, do not return in any subsequent queries.
        """
        query = self.table.select().where(self.table.c.userid == userid).where(self.table.c.keyid == keyid)
        record = await self.database.fetch_one(query=query)
        if record is None:
            return None
        key = KeyInDB(**record)
        if key.deleted:
            # key has been deleted
            return None
        return key

    async def get_all(self, userid: UUID4) -> AllKeysInDB:
        """
        If the key was deleted by the user, do not return in any subsequent queries.
        """
        query = self.table.select().where(self.table.c.userid == userid)
        records = await self.database.fetch_all(query=query)
        if not records:
            return AllKeysInDB(keys=[])
        return AllKeysInDB(keys=({**record} for record in records if record.get("deleted") is False))

    async def create(self, userid: UUID4, description: str) -> Optional[tuple[NewKey, str]]:
        """
        description: verify beforehand that the length of description is less than 255
        """
        client_secret, secret_hash = self.generate_client_secret()
        value = {
            "userid": userid,
            "keypass": secret_hash,
            "description": description,
        }
        query = (
            self.table.insert()
            .values(value)
            .returning(
                self.table.c.userid,
                self.table.c.keyid,
                self.table.c.description,
            )
        )
        # avoid using database.execute() or database.execute_many(), some
        # return values are being discarded
        newkey = await self.database.fetch_one(query=query)
        return (NewKey(**newkey), client_secret)

    async def toogle(self, userid: UUID4, keyid: UUID4, disabled: bool) -> Optional[bool]:
        async with self.database.transaction():
            key = await self.get(userid, keyid)
            if key is None:
                # No mactching key found
                return None
            if key.frozen:
                # Key was frozen by admin
                return None
            if disabled and key.disabled:
                # Key is already disabled
                return False
            if not disabled and not key.disabled:
                # Key is already enabled
                return False

            query = (
                self.table.update()
                .where(self.table.c.userid == userid)
                .where(self.table.c.keyid == keyid)
                .values({"disabled": disabled})
                .returning(self.table.c.disabled)
            )
            result = await self.database.fetch_one(query=query)
            if result is None:
                # this should never happen as we have already checked the existence of key
                # and we are doing a transaction.
                return None

            enabled = result.get("disabled", disabled)
            if enabled == (not disabled):
                # toogle successfull
                return True
            else:
                # this should never happen
                return False

    async def disable(self, userid: UUID4, keyid: UUID4) -> Optional[bool]:
        # TODO: How to disable the key associated with an active API
        return await self.toogle(userid, keyid, disabled=True)

    async def enable(self, userid: UUID4, keyid: UUID4) -> Optional[bool]:
        return await self.toogle(userid, keyid, disabled=False)

    async def delete(self, userid: UUID4, keyid: UUID4) -> Optional[bool]:
        async with self.database.transaction():
            key = await self.get(userid, keyid)
            if key is None:
                # No mactching key found
                return None
            if key.frozen:
                # Key was frozen by admin
                return None

            query = (
                self.table.update()
                .where(self.table.c.userid == userid)
                .where(self.table.c.keyid == keyid)
                .values({"deleted": True})
                .returning(self.table.c.deleted)
            )
            result = await self.database.fetch_one(query=query)
            if result is None:
                # this should never happen as we have already checked the existence
                # of key and we are doing a transaction.
                return None

            if result.get("deleted") is True:
                return True
            # thi should never happen
            return False
