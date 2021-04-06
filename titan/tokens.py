import uuid
from datetime import datetime, timedelta
from enum import Enum, unique
from typing import Optional, Union

from jose import jwt
from jose.exceptions import JOSEError, JWTError
from pydantic import UUID4, validator, ValidationError

from .logger import logger
from .settings.jwt import get_jwt_config
from .utils import ImmutBaseModel

# token issuer
TOKEN_ISS = "episense.ai"


@unique
class TokenType(str, Enum):
    ACCESS_TOKEN = "axx"
    REFRESH_TOKEN = "rxx"
    XACCESS_TOKEN = "xxx"


class EncodedToken(ImmutBaseModel):
    token: str
    expires_in: Optional[int] = None


class Token(ImmutBaseModel):
    token_type: str = "Bearer"


class XAccessToken(Token):
    access_token: str
    expires_in: int


class AccessToken(Token):
    access_token: str
    expires_in: int
    refresh_token: Optional[str] = None


class RefreshToken(Token):
    refresh_token: str


# https://tools.ietf.org/html/rfc7519#page-9
class TokenClaims(ImmutBaseModel):
    sub: UUID4
    aud: Optional[str] = None
    scope: str = ""

    @validator("scope", pre=True)
    def join_scope(cls, values):
        """
        Join the list of scope into a space separated string of scope
        """
        if isinstance(values, list):
            return " ".join(values)
        return values

    def issue(self, ttype: TokenType) -> EncodedToken:
        config = get_jwt_config()

        current_time = datetime.utcnow()

        if ttype == TokenType.ACCESS_TOKEN:
            exp = current_time + config.authjwt_access_token_expires
            expires_in = int(config.authjwt_access_token_expires / timedelta(seconds=1)) - 10
        elif ttype == TokenType.REFRESH_TOKEN:
            exp = current_time + config.authjwt_refresh_token_expires
            expires_in = None
        elif ttype == TokenType.XACCESS_TOKEN:
            exp = current_time + config.authjwt_xaccess_token_expires
            expires_in = int(config.authjwt_xaccess_token_expires / timedelta(seconds=1)) - 10
        else:
            raise RuntimeError(f"Can not issue token of {ttype=}")

        claims_dict = {}

        claims_dict.update(sub=self.sub.hex, scope=self.scope)
        if self.aud:
            claims_dict.update(aud=self.aud)

        # custom claims
        claims_dict.update(ttype=ttype.value)

        # reserved claims
        claims_dict.update(iss=TOKEN_ISS, exp=exp)

        token = jwt.encode(
            claims_dict,
            config.get_secret_key("encode"),
            algorithm=config.authjwt_algorithm,
        )

        return EncodedToken(token=token, expires_in=expires_in)

    def issue_access_token(self) -> AccessToken:
        atoken = self.issue(TokenType.ACCESS_TOKEN)

        return AccessToken(
            access_token=atoken.token,
            expires_in=atoken.expires_in,
        )

    def issue_refresh_token(self) -> RefreshToken:
        rtoken = self.issue(TokenType.REFRESH_TOKEN)
        return RefreshToken(refresh_token=rtoken.token)

    def issue_access_refresh_token(self) -> AccessToken:
        atoken = self.issue(TokenType.ACCESS_TOKEN)
        rtoken = self.issue(TokenType.REFRESH_TOKEN)

        return AccessToken(
            access_token=atoken.token,
            expires_in=atoken.expires_in,
            refresh_token=rtoken.token,
        )

    def issue_xaccess_token(self) -> XAccessToken:
        xtoken = self.issue(TokenType.XACCESS_TOKEN)

        return XAccessToken(
            access_token=xtoken.token,
            expires_in=xtoken.expires_in,
        )


class DecodedToken(ImmutBaseModel):
    sub: UUID4
    scope: Union[str, list[str]]
    ttype: TokenType


async def validate_token(raw_token: str) -> Optional[DecodedToken]:
    config = get_jwt_config()

    try:
        decoded_token = jwt.decode(
            raw_token,
            config.get_secret_key("decode"),
            algorithms=config.authjwt_algorithm,
            options={
                "require_exp": True,
                "require_sub": True,
                "require_iss": True,
                "require_jti": False,
            },
            issuer=TOKEN_ISS,
        )
        logger.info(f"Decoded Bearer token for sub={decoded_token['sub']}")
        return DecodedToken(**decoded_token)
    except (JWTError, JOSEError) as exc:
        logger.error(f"JWT decode error: {exc}")
        return None
    except ValidationError as exc:
        logger.error(f"JWT token decode error: {exc}")
        return None
    except Exception:
        logger.exception("Unknown JWT decode error")
        return None
