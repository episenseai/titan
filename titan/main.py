from .jwt_token import JWTTokenClaims
from jose import jwt
from .config import get_auth_config
from pprint import pprint

print = pprint

if __name__ == "__main__":
    auth_config = get_auth_config()
    decode = lambda token: jwt.decode(
        token, auth_config.get_secret_key("decode"), algorithms=[auth_config.authjwt_algorithm]
    )

    claims = JWTTokenClaims(sub="sushant", iss="episense")
    print(decode(claims.mint_access_token().access_token))
    print(decode(claims.mint_refresh_token().refresh_token))
    print(claims.mint_access_refresh_token())
