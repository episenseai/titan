import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Sequence, Union

from jose import jwt
from jose.exceptions import JOSEError, JWTError
from pydantic import validator
from pydantic.types import StrictInt, StrictStr

from ..models import ImmutBaseModel
from .config import get_jwt_config


class EncodedJWTToken(ImmutBaseModel):
    token: str
    expires_in: Optional[int] = None


class Token(ImmutBaseModel):
    pass


class AccessToken(Token):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    userid: Optional[str] = None
    full_name: Optional[str] = None


class RefreshToken(Token):
    refresh_token: str


TOKEN_ISS = "https://episense.ai"

# https://tools.ietf.org/html/rfc7519#page-9
class TokenClaims(ImmutBaseModel):
    # subject
    sub: Union[StrictStr, StrictInt]
    # issuer
    iss: Optional[Union[StrictStr, StrictInt]]
    # audience
    aud: Optional[Union[StrictStr, Sequence[StrictStr]]] = None
    # scope
    scope: Union[StrictStr, List[StrictStr]] = ""

    @validator("scope", pre=True)
    def join_scope(cls, values):
        """
        Join the list of scope into a space separated string of scope
        """
        if isinstance(values, list):
            return " ".join(values)
        return values

    def _mint_token(self, ttype: str) -> EncodedJWTToken:
        config = get_jwt_config()

        current_time = datetime.utcnow()
        if ttype == "access_token":
            exp = current_time + config.authjwt_access_token_expires
            expires_in = int(config.authjwt_access_token_expires / timedelta(seconds=1)) - 10
        elif ttype == "refresh_token":
            exp = current_time + config.authjwt_refresh_token_expires
            expires_in = None
        else:
            raise RuntimeError("Can not issue token")

        custom_claims = {}
        custom_claims["ttype"] = ttype

        reserved_claims = {"iss": TOKEN_ISS, "exp": exp, "jti": str(uuid.uuid4())}

        token = jwt.encode(
            {**self.dict(exclude_none=True), **custom_claims, **reserved_claims},
            config.get_secret_key("encode"),
            algorithm=config.authjwt_algorithm,
        )

        return EncodedJWTToken(token=token, expires_in=expires_in)

    def mint_access_token(self, userid: Optional[str] = None, full_name: Optional[str] = None) -> AccessToken:
        encoded_token = self._mint_token("access_token")
        return AccessToken(
            access_token=encoded_token.token,
            token_type="Bearer",
            expires_in=encoded_token.expires_in,
            userid=userid,
            full_name=full_name,
        )

    def mint_refresh_token(self) -> RefreshToken:
        encoded_token = self._mint_token("refresh_token")
        return RefreshToken(refresh_token=encoded_token.token)

    def mint_access_refresh_token(self, userid: Optional[str] = None, full_name: Optional[str] = None) -> AccessToken:
        atoken = self._mint_token("access_token")
        rtoken = self._mint_token("refresh_token")
        return AccessToken(
            access_token=atoken.token,
            token_type="Bearer",
            expires_in=atoken.expires_in,
            refresh_token=rtoken.token,
            userid=userid,
            full_name=full_name,
        )


async def validate_and_get_token_claims_dict(raw_token: str) -> Optional[dict]:
    config = get_jwt_config()

    try:
        decoded_token = jwt.decode(
            raw_token,
            config.get_secret_key("decode"),
            algorithms=config.authjwt_algorithm,
            options={
                "require_exp": True,
                "require_sub": True,
                "require_jti": True,
                "require_iss": True,
            },
            issuer=TOKEN_ISS,
        )
        return decoded_token
    except (JWTError, JOSEError):
        return None
