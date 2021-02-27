import uuid
from datetime import datetime
from typing import Optional, Sequence, Union

from jose import jwt
from jose.exceptions import JOSEError, JWTError
from pydantic.types import StrictInt, StrictStr

from .config import get_auth_config
from ..model import ImmutBaseModel


class UnverifiedJWTToken(ImmutBaseModel):
    token: str


class EncodedJWTToken(ImmutBaseModel):
    token: str


class AccessToken(ImmutBaseModel):
    access_token: str
    token_type: str


class RefreshToken(ImmutBaseModel):
    refresh_token: str


class AccessRefreshToken(AccessToken, RefreshToken):
    pass


# https://tools.ietf.org/html/rfc7519#page-9
class TokenClaims(ImmutBaseModel):
    # subject
    sub: Optional[Union[StrictStr, StrictInt]] = None
    # issuer
    iss: Optional[Union[StrictStr, StrictInt]] = None
    # audience
    aud: Optional[Union[StrictStr, Sequence[StrictStr]]] = None
    # scopes
    scopes: Optional[StrictStr] = None

    def _mint_token(self, ttype: str) -> EncodedJWTToken:
        config = get_auth_config()

        if ttype == "access_token":
            exp = datetime.utcnow() + config.authjwt_access_token_expires
        elif ttype == "refresh_token":
            exp = datetime.utcnow() + config.authjwt_refresh_token_expires
        else:
            raise RuntimeError("Can not issue token")

        custom_claims = {}
        custom_claims["ttype"] = ttype

        reserved_claims = {"exp": exp, "jti": str(uuid.uuid4())}

        token = jwt.encode(
            {**self.dict(exclude_none=True), **custom_claims, **reserved_claims},
            config.get_secret_key("encode"),
            algorithm=config.authjwt_algorithm,
        )
        return EncodedJWTToken(token=token)

    def mint_access_token(self) -> AccessToken:
        encoded_token = self._mint_token("access_token")
        return AccessToken(access_token=encoded_token.token, token_type="Bearer")

    def mint_refresh_token(self) -> RefreshToken:
        encoded_token = self._mint_token("refresh_token")
        return RefreshToken(refresh_token=encoded_token.token)

    def mint_access_refresh_token(self) -> AccessRefreshToken:
        atoken = self.mint_access_token()
        rtoken = self.mint_refresh_token()
        return AccessRefreshToken(**atoken.dict(), **rtoken.dict())

    class Config:
        min_anystr_length = 1


async def validate_and_get_token_claims_dict(raw_token: UnverifiedJWTToken) -> Optional[dict]:
    config = get_auth_config()
    try:
        decoded_token = jwt.decode(
            raw_token.token,
            config.get_secret_key("decode"),
            algorithm=config.authjwt_algorithm,
        )
        return decoded_token
    except (JWTError, JOSEError):
        return None
