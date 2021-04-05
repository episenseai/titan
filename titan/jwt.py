import uuid
from datetime import datetime, timedelta
from typing import Optional, Sequence, Union

from jose import jwt
from jose.exceptions import JOSEError, JWTError
from pydantic import UUID4, validator
from pydantic.types import StrictInt, StrictStr

from .logger import logger
from .settings.jwt import get_jwt_config
from .utils import ImmutBaseModel


class EncodedJWTToken(ImmutBaseModel):
    token: str
    expires_in: Optional[int] = None


class Token(ImmutBaseModel):
    pass


class XAccessToken(Token):
    access_token: str
    token_type: str
    expires_in: int
    userid: Optional[str] = None


class AccessToken(Token):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    userid: Optional[str] = None
    full_name: Optional[str] = None
    picture: Optional[str] = None
    # some user state that was supplied at the start of the login flow
    ustate: Optional[str] = None


class RefreshToken(Token):
    refresh_token: str


TOKEN_ISS = "https://episense.ai"

# https://tools.ietf.org/html/rfc7519#page-9
class TokenClaims(ImmutBaseModel):
    # subject
    sub: Union[StrictStr, StrictInt]
    # audience
    aud: Optional[Union[StrictStr, Sequence[StrictStr]]] = None
    # scope
    scope: Union[StrictStr, list[StrictStr]] = ""

    @validator("scope", pre=True)
    def join_scope(cls, values):
        """
        Join the list of scope into a space separated string of scope
        """
        if isinstance(values, list):
            return " ".join(values)
        return values

    def mint(self, ttype: str) -> EncodedJWTToken:
        config = get_jwt_config()

        current_time = datetime.utcnow()

        if ttype == "access_token":
            exp = current_time + config.authjwt_access_token_expires
            expires_in = int(config.authjwt_access_token_expires / timedelta(seconds=1)) - 10
        elif ttype == "refresh_token":
            exp = current_time + config.authjwt_refresh_token_expires
            expires_in = None
        elif ttype == "xaccess_token":
            exp = current_time + config.authjwt_xaccess_token_expires
            expires_in = int(config.authjwt_xaccess_token_expires / timedelta(seconds=1)) - 10
        else:
            raise RuntimeError("Can not issue token")

        # token claims
        claims = {}
        # sub + aud + scope claims
        claims.update(self.dict(exclude_none=True))
        # custom claims
        claims.update(ttype=ttype)
        # reserved_claims
        claims.update({"iss": TOKEN_ISS, "exp": exp, "jti": uuid.uuid4().hex})

        token = jwt.encode(claims, config.get_secret_key("encode"), algorithm=config.authjwt_algorithm)

        return EncodedJWTToken(token=token, expires_in=expires_in)

    def mint_access_token(
        self, full_name: Optional[str] = None, picture: Optional[str] = None, ustate: Optional[str] = None
    ) -> AccessToken:
        encoded_token = self.mint("access_token")

        return AccessToken(
            access_token=encoded_token.token,
            token_type="Bearer",
            expires_in=encoded_token.expires_in,
            userid=str(self.sub),
            full_name=full_name,
            picture=picture,
            ustate=ustate,
        )

    def mint_refresh_token(self) -> RefreshToken:
        encoded_token = self.mint("refresh_token")
        return RefreshToken(refresh_token=encoded_token.token)

    def mint_access_refresh_token(
        self, full_name: Optional[str] = None, picture: Optional[str] = None, ustate: Optional[str] = None
    ) -> AccessToken:
        atoken = self.mint("access_token")
        rtoken = self.mint("refresh_token")

        return AccessToken(
            access_token=atoken.token,
            token_type="Bearer",
            expires_in=atoken.expires_in,
            refresh_token=rtoken.token,
            userid=str(self.sub),
            full_name=full_name,
            picture=picture,
            ustate=ustate,
        )

    def mint_xaccess_token(self) -> XAccessToken:
        encoded_token = self.mint("xaccess_token")

        return XAccessToken(
            access_token=encoded_token.token,
            token_type="Bearer",
            expires_in=encoded_token.expires_in,
            userid=str(self.sub),
        )


class DecodedToken(ImmutBaseModel):
    sub: UUID4
    scope: str
    ttype: str
    jti: UUID4


async def validate_get_decoded_token(raw_token: str) -> Optional[DecodedToken]:
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
        logger.info(f"Decoded Bearer token for sub={decoded_token['sub']}")
        return DecodedToken(**decoded_token)
    except (JWTError, JOSEError) as exc:
        logger.error(f"JWT decode error: {exc}")
        return None
    except Exception:
        logger.exception("Unknown JWT decode error")
        return None
