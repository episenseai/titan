from typing import Any, Dict, Optional, Tuple, Union, List
from datetime import datetime, timedelta
from jose import jwt
from jose.exceptions import JOSEError
from devtools import debug
from urllib.parse import urlencode
import httpx
from ..exceptions import JWTDecodeError, Oauth2AuthorizationError, JSONDecodeError

from pydantic import AnyHttpUrl, SecretStr
from fastapi import HTTPException, status

from .models import IdP, OAuth2AuthClient, OAuth2LoginClient, OAuth2AuthentcatedUser
from .state import StateToken

# get the values from
# https://accounts.google.com/.well-known/openid-configuration
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_JWKS_URI = "https://www.googleapis.com/oauth2/v3/certs"


class GoogleLoginClient(OAuth2LoginClient):
    @staticmethod
    def new(
        client_id: str,
        scope: str,
        redirect_uri: Union[AnyHttpUrl, str],
        iss: Optional[str] = None,
    ) -> OAuth2LoginClient:
        """
        Builder method to create an instance of the class
        """
        return GoogleLoginClient(
            auth_url=GOOGLE_AUTH_URL,
            token_url=GOOGLE_TOKEN_URL,
            jwks_uri=GOOGLE_JWKS_URI,
            client_id=client_id,
            scope=scope,
            redirect_uri=redirect_uri,
            iss=iss,
        )

    @property
    def idp(self) -> IdP:
        return IdP.google

    def get_query_params(self, token: StateToken, refresh_token: bool = False) -> Dict[str, Any]:
        if refresh_token:
            access_type = "offline"
        else:
            access_type = "online"
        url_params = {
            "response_type": "code",
            "client_id": self.client_id,
            "scope": self.scope,
            "redirect_uri": self.redirect_uri,
            "access_type": access_type,
            "state": token.state,
        }
        # nonce is present if using OpenId Connect to get the id_token
        if token.nonce is not None:
            url_params.update({"nonce": token.nonce})
        print(f"{url_params=}")
        return url_params

    def get_urlencoded_query_params(self, token: StateToken, refresh_token: bool) -> str:
        return urlencode(self.get_query_params(token, refresh_token))

    def create_auth_url(self, token: StateToken, refresh_token: bool = False) -> str:
        encoded_params = self.get_urlencoded_query_params(token, refresh_token)
        return f"{str(self.auth_url)}?{encoded_params}"


class GoogleAuthClient(OAuth2AuthClient):
    @staticmethod
    def new(
        client_id: str,
        scope: str,
        redirect_uri: Union[AnyHttpUrl, str],
        client_secret: Union[SecretStr, str],
        iss: Optional[str] = None,
    ) -> OAuth2AuthClient:
        """
        Builder method to create an instance of the class
        """
        return GoogleAuthClient(
            auth_url=GOOGLE_AUTH_URL,
            token_url=GOOGLE_TOKEN_URL,
            jwks_uri=GOOGLE_JWKS_URI,
            client_id=client_id,
            scope=scope,
            redirect_uri=redirect_uri,
            client_secret=client_secret,
            iss=iss,
        )

    @property
    def idp(self) -> IdP:
        return IdP.github

    def get_query_params(self, code: str, token: StateToken) -> Dict[str, Any]:
        url_params = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret.get_secret_value(),
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }
        return url_params

    def get_urlencoded_query_params(self, code: str, token: StateToken) -> str:
        return urlencode(self.get_query_params(code, token))

    def validate_requested_scope(self, granted_scope: Union[str, List[str]]) -> bool:
        raise NotImplementedError("GoogleAuthClient validate_requested_scope not implemented")

    async def update_jwks_keys(self):
        if self.jwks_uri is None:
            raise ValueError("Missing 'jwks_uri' key in GoogleAuthClient")

        keys = self.jwks_keys.get("keys", None)
        expiration_datetime = self.jwks_keys.get("expiration_datetime", None)
        if keys is not None and expiration_datetime is not None:
            if datetime.utcnow() <= expiration_datetime:
                return

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(str(self.jwks_uri))
                if response.status_code == httpx.codes.OK:
                    try:
                        jwks_keys = response.json()
                        expiration_datetime = datetime.utcnow() + timedelta(hours=1)
                        self.jwks_keys.update({"expiration_datetime": expiration_datetime})
                    except Exception as exc:
                        raise JSONDecodeError(f"Error decoding keys from {self.jwks_uri=}")
                    # update with freshly downloaded keys
                    self.jwks_keys.update(jwks_keys)
                elif self.jwks_keys.get("keys", None):
                    raise RuntimeError(f"Error instantiating 'jwks_keys' from {self.jwks_uri=}")
                else:
                    print(f"WARINING: using stale keys. Unable to reach {self.jwks_uri}")
            except httpx.RequestError as exc:
                raise Oauth2AuthorizationError(f"Error calling {exc.request.url} endpoint") from exc

    async def validate_id_token(self, jwt_token: str, access_token: str) -> Dict[str, Any]:
        await self.update_jwks_keys()
        keys = self.jwks_keys.get("keys", None)
        if not keys:
            RuntimeError("Somethin fatal happened: 'jwks_keys' keys are missing for google")
        try:
            success = False
            for key in keys:
                try:
                    print(jwt_token, "\n\n")
                    print(access_token)
                    options = {
                        "verify_signature": True,
                        "verify_aud": False,
                        "verify_iat": False,
                        "verify_exp": True,
                        "verify_nbf": True,
                        "verify_iss": True,
                        "verify_sub": False,
                        "verify_at_hash": True,
                    }
                    data = jwt.decode(
                        jwt_token,
                        key,
                        options=options,
                        audience=self.client_id,
                        access_token=access_token,
                    )
                    debug(data)
                    success = True
                    break
                except JOSEError as exc:
                    pass
            if not success:
                raise JWTDecodeError("Error validating 'id_token'. None of 'jwks_keys' worked.")
            return data
        except Exception as exc:
            raise Oauth2AuthorizationError(f"Unknown Error during 'id_token' validation for google {exc=}")

    async def authorize(self, code: str, token: StateToken) -> OAuth2AuthentcatedUser:
        async with httpx.AsyncClient() as client:
            try:
                params = self.get_query_params(code, token)
                response = await client.post(str(self.token_url), params=params)
                debug(response, response.request, response.headers, response.text)
                response.raise_for_status()
            except httpx.RequestError as exc:
                raise Oauth2AuthorizationError(f"Resquest Error for token from google {exc.request}") from exc
            except Exception as exc:
                raise Oauth2AuthorizationError(
                    f"Response code != 20x for token request from google {exc.response}"
                ) from exc

        try:
            auth_response: dict = response.json()
            debug(auth_response)
        except Exception as exc:
            raise JSONDecodeError("Error decoding token reponse (JSON) from github") from exc

        for key in ("access_token", "token_type", "scope", "expires_in"):
            if key not in auth_response:
                raise Oauth2AuthorizationError(f"Missing '{key}' in token reponse from github")

        token_type: str = auth_response.get("token_type")
        if not token_type or token_type.lower() != "bearer":
            raise Oauth2AuthorizationError(f"{token_type=} != 'bearer' for token response from google")

        user_dict = {}

        # nonce parameter is present for OpenId Connect
        if token.nonce is not None:
            id_token = auth_response.get("id_token", None)
            if id_token is None:
                raise Oauth2AuthorizationError("Missing 'id_token' in auth_response from google")
            else:
                access_token = auth_response.get("access_token")
                user_dict = await self.validate_id_token(id_token, access_token)
        if token.nonce != user_dict.get("nonce", None):
            raise Oauth2AuthorizationError("Error 'nonce' value in the id_token did not match stored value")

        # return OAuth2AuthentcatedUser
        raise NotImplementedError()

    def user(self, user_dict: dict, auth_dict: dict) -> OAuth2AuthentcatedUser:
        pass
