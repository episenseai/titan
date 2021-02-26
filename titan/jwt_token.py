import uuid
from datetime import datetime
from typing import Optional, Sequence, Union

from jose import jwt
from pydantic import BaseModel
from pydantic.types import StrictInt, StrictStr

from .config import get_auth_config


class JWTAccessToken(BaseModel):
    access_token: str
    token_type: str


class JWTRefreshToken(BaseModel):
    refresh_token: str


class JWTAccessRefreshToken(JWTAccessToken, JWTRefreshToken):
    pass


class JWTTokenClaims(BaseModel):
    # subject
    sub: Optional[Union[StrictStr, StrictInt]] = None
    # issuer
    iss: Optional[Union[StrictStr, StrictInt]] = None
    # audience
    aud: Optional[Union[StrictStr, Sequence[StrictStr]]] = None
    # scopes
    scopes: Optional[StrictStr] = None

    def _mint_token(self, ttype: str) -> str:
        auth_config = get_auth_config()

        if ttype == "access_token":
            exp = datetime.utcnow() + auth_config.authjwt_access_token_expires
        elif ttype == "refresh_token":
            exp = datetime.utcnow() + auth_config.authjwt_refresh_token_expires
        else:
            raise RuntimeError("Can not issue token")

        reserved_claims = {"exp": exp, "jti": str(uuid.uuid4())}

        encoded_jwt = jwt.encode(
            {**self.dict(exclude_none=True), **reserved_claims},
            auth_config.get_secret_key("encode"),
            algorithm=auth_config.authjwt_algorithm,
        )
        return encoded_jwt

    def mint_access_token(self) -> JWTAccessToken:
        return JWTAccessToken(access_token=self._mint_token("access_token"), token_type="Bearer")

    def mint_refresh_token(self) -> JWTRefreshToken:
        return JWTRefreshToken(refresh_token=self._mint_token("refresh_token"))

    def mint_access_refresh_token(self) -> JWTAccessRefreshToken:
        atoken = self.mint_access_token()
        rtoken = self.mint_refresh_token()
        return JWTAccessRefreshToken(
            access_token=atoken.access_token, token_type=atoken.token_type, refresh_token=rtoken.refresh_token
        )

    class Config:
        min_anystr_length = 1
        # faux immutability of fields
        allow_mutation = False
