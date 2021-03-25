from typing import Optional

from databases import Database

from ..exceptions import DatabaseUserFetchError
from .schema.apis import ApiInDB, apis_schema

# from passlib.context import CryptContext

# ["auto"] will configure the CryptContext instance to deprecate all
# supported schemes except for the default scheme.
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", truncate_error=True)


class ApisTable:
    pass
