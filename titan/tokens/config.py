from datetime import timedelta
from functools import lru_cache
from typing import Optional

from pydantic import root_validator, validator
from pydantic.types import StrictBool, StrictStr

from ..models import ImmutBaseModel

# In the real case, you can put the
# public key and private key in *.pem, *.key then you can read that file
private_key = """
-----BEGIN RSA PRIVATE KEY-----
MIICWwIBAAKBgGBoQhqHdMU65aSBQVC/u9a6HMfKA927aZOk7HA/kXuA5UU4Sl+U
C9WjDhMQFk1PpqAjZdCqx9ajolTYnIfeaVHcLNpJQ6QXLnUyMnfwPmwYQ2rkuy5w
I2NdO81CzJ/9S8MsPyMl2/CF9ZxM03eleE8RKFwXCxZ/IoiqN4jVNjSrAgMBAAEC
gYAnNqEUq146zx8TT6PilWpxB9inByuVaCKkdGPbsG+bfa1D/4Z44/4AUsdpx5Ra
s/hBkMRcIOsSChMAUe8xcK0DqA9Y7BIVfpma2fH/gYq6dP3dOfCxftZBF00HwIu7
5e7RWnBC8MkPnrkKdHq6ptAYlGgoSJTEQREqusDiuNG9yQJBAKQib2VhNAqgyvvi
PdmFrCqq15z9MY16WCfttuqfAaSYKHnZe1WvBKbSNW9x4Cgjfhzl9mlozlW4rob/
ttPN6e0CQQCWXbVtqmVdB5Ol9wQN7DIRc8q5F8HKQqIJAMTmwaRwNDsGRxCWMwGO
8WAlnejzYTXmrrytv6kXX8U40enJW2X3AkAI42h+5/WmgbCcVVMeHXQGV3wXn0p4
q+BsQR4/tF6laCwA9TsNl827rvR/1X3bDpj8vaNLcAaEc9zXqK9g5uy9AkATeOkw
3Xso8/075eRBhU/qkKs1Ew2GiuB+9/mHxJXt7eWi53sPaGWQRFPmKy/qrLEVQZWv
jn1wSHe65vw2lj57AkEAh04n1wrZnCha8s6crMhjggdTXI6G4FU3TGf8ssGboqs3
j5lemvyKod+u2JVKwarcKmd/gFYBOjsRm18LlZH74A==
-----END RSA PRIVATE KEY-----
"""
public_key = """
-----BEGIN PUBLIC KEY-----
MIGeMA0GCSqGSIb3DQEBAQUAA4GMADCBiAKBgGBoQhqHdMU65aSBQVC/u9a6HMfK
A927aZOk7HA/kXuA5UU4Sl+UC9WjDhMQFk1PpqAjZdCqx9ajolTYnIfeaVHcLNpJ
Q6QXLnUyMnfwPmwYQ2rkuy5wI2NdO81CzJ/9S8MsPyMl2/CF9ZxM03eleE8RKFwX
CxZ/IoiqN4jVNjSrAgMBAAE=
-----END PUBLIC KEY-----
"""

symmetric_crypto = {"HS256", "HS384", "HS512"}
asymetric_crypto = {
    "RS256",
    "RS384",
    "RS512",
    "ES256",
    "ES384",
    "ES521",
    "ES512",
    "PS256",
    "PS384",
    "PS512",
    "EdDSA",
}


class __AuthSettings(ImmutBaseModel):
    authjwt_algorithm: StrictStr = "RS512"
    authjwt_secret_key: Optional[StrictStr] = None
    authjwt_public_key: Optional[StrictStr] = public_key
    authjwt_private_key: Optional[StrictStr] = private_key
    authjwt_access_token_expires: timedelta = timedelta(minutes=240)
    authjwt_refresh_token_expires: timedelta = timedelta(hours=8)
    authjwt_xaccess_token_expires: timedelta = timedelta(hours=1)
    authjwt_denylist_enabled: StrictBool = False
    authjwt_denylist_token_types: set[StrictStr] = {"access_token", "refresh_token"}

    @validator("authjwt_algorithm", always=True)
    def validate_algorithm(cls, v):
        if v not in symmetric_crypto and v not in asymetric_crypto:
            raise RuntimeError(f"authjwt_algorithm = '{v}' not in supported symmetric/asymetric list")
        return v

    @validator("authjwt_denylist_token_types", each_item=True, always=True)
    def validate_denylist(cls, v):
        authjwt_denylist_token_types = {"access_token", "refresh_token"}
        if v not in authjwt_denylist_token_types:
            raise RuntimeError(f"allowed {authjwt_denylist_token_types=}")
        return v

    @root_validator(pre=False)
    def validate_algo_keys(cls, values):
        algo = values.get("authjwt_algorithm")
        if algo in asymetric_crypto:
            if values.get("authjwt_public_key") is None:
                raise RuntimeError("authjwt_public_key not provided")
            if values.get("authjwt_private_key") is None:
                raise RuntimeError("authjwt_private_key not provided")
        if algo in symmetric_crypto:
            if values.get("authjwt_secret_key") is None:
                raise RuntimeError("authjwt_secret_key not provided")
        return values

    @root_validator(pre=False)
    def token_expires(cls, values):
        if values.get("authjwt_access_token_expires") >= values.get("authjwt_refresh_token_expires"):
            raise RuntimeError("authjwt_access_token_expires must be less than authjwt_refresh_token_expires")
        return values

    def get_secret_key(self, method: Optional[str] = None):
        if self.authjwt_algorithm in asymetric_crypto:
            if method == "encode":
                return self.authjwt_private_key
            elif method == "decode":
                return self.authjwt_public_key
            else:
                raise RuntimeError(f"unsupported_method = {method} for jwt")
        elif self.authjwt_algorithm in symmetric_crypto:
            return self.authjwt_secret_key
        else:
            raise RuntimeError(f"Unsupported algorithm = {self.authjwt_algorithm} for jwt")


@lru_cache
def get_jwt_config() -> __AuthSettings:
    return __AuthSettings()


get_jwt_config()
