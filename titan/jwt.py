import uuid
from datetime import datetime, timedelta
from typing import Optional, Sequence, Union

from jose import jwt
from jose.exceptions import JOSEError, JWTError
from pydantic import validator
from pydantic.types import StrictInt, StrictStr

from .auth.state import StateToken
from .models.admins import AdminInDB
from .models.users import UserInDB
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
    u: Optional[str] = None


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
    scope: Union[StrictStr, list[StrictStr]] = ""

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
        elif ttype == "xaccess_token":
            exp = current_time + config.authjwt_xaccess_token_expires
            expires_in = int(config.authjwt_xaccess_token_expires / timedelta(seconds=1)) - 10
        else:
            raise RuntimeError("Can not issue token")

        custom_claims = {}
        custom_claims["ttype"] = ttype

        reserved_claims = {"iss": TOKEN_ISS, "exp": exp, "jti": uuid.uuid4().hex}

        token = jwt.encode(
            {**self.dict(exclude_none=True), **custom_claims, **reserved_claims},
            config.get_secret_key("encode"),
            algorithm=config.authjwt_algorithm,
        )

        return EncodedJWTToken(token=token, expires_in=expires_in)

    def mint_access_token(
        self,
        user: UserInDB,
        token: Optional[StateToken] = None,
    ) -> AccessToken:
        encoded_token = self._mint_token("access_token")
        if token:
            u = token.uistate
        else:
            u = None
        return AccessToken(
            access_token=encoded_token.token,
            token_type="Bearer",
            expires_in=encoded_token.expires_in,
            userid=str(user.userid),
            full_name=user.full_name,
            picture=user.picture,
            u=u,
        )

    def mint_refresh_token(self) -> RefreshToken:
        encoded_token = self._mint_token("refresh_token")
        return RefreshToken(refresh_token=encoded_token.token)

    def mint_access_refresh_token(
        self,
        user: UserInDB,
        token: Optional[StateToken] = None,
    ) -> AccessToken:
        atoken = self._mint_token("access_token")
        rtoken = self._mint_token("refresh_token")
        if token:
            u = token.uistate
        else:
            u = None
        return AccessToken(
            access_token=atoken.token,
            token_type="Bearer",
            expires_in=atoken.expires_in,
            refresh_token=rtoken.token,
            userid=str(user.userid),
            full_name=user.full_name,
            picture=user.picture,
            u=u,
        )

    def mint_xaccess_token(self, admin: AdminInDB):
        encoded_token = self._mint_token("xaccess_token")

        return XAccessToken(
            access_token=encoded_token.token,
            token_type="Bearer",
            expires_in=encoded_token.expires_in,
            userid=str(admin.adminid),
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
    except (JWTError, JOSEError) as exc:
        print(exc)
        return None
