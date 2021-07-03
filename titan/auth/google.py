from datetime import datetime, timedelta
from typing import Any, Optional, Union
from urllib.parse import urlencode

import httpx
from jose import jwt
from jose.exceptions import JOSEError
from pydantic import AnyHttpUrl, SecretStr

from ..exceptions.exc import Oauth2AuthError, OAuth2EmailPrivdedError
from ..logger import logger
from .models import IdentityProvider, OAuth2AuthClient, OAuth2AuthentcatedUser, OAuth2LoginClient
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
    def idp(self) -> IdentityProvider:
        return IdentityProvider.google

    def get_query_params(self, token: StateToken, refresh_token: bool = False) -> dict[str, Any]:
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
    def idp(self) -> IdentityProvider:
        return IdentityProvider.google

    def get_query_params(self, code: str, token: StateToken) -> dict[str, Any]:
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

    async def update_jwks_keys(self):
        keys = self.jwks_keys.get("keys", None)
        expiration_datetime = self.jwks_keys.get("expiration_datetime", None)
        if keys is not None and expiration_datetime is not None:
            if datetime.utcnow() <= expiration_datetime:
                return

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(str(self.jwks_uri))
                response.raise_for_status()
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                err_msg = f"Google JWS keys endpoint: {exc=} {exc.request.url}"
                logger.error(err_msg)
                raise Oauth2AuthError(err_msg) from exc
            except Exception as exc:
                err_msg = f"Unexpected: Google JWS keys endpoint: {exc=} {exc.request.url}"
                logger.exception(err_msg)
                raise Oauth2AuthError(err_msg) from exc

            try:
                jwks_keys = response.json()
            except Exception as exc:
                err_msg = f"Google JWS keys decode: {exc}"
                logger.exception(err_msg)
                raise Oauth2AuthError(err_msg)

            # Update stale JWS keys with freshly downloaded ones
            self.jwks_keys.update(jwks_keys)
            self.jwks_keys.update(
                {"expiration_datetime": datetime.utcnow() + timedelta(hours=1)},
            )

            logger.info("Fetched Google JWKS keys")

    async def validate_id_token(self, jwt_token: str, access_token: str) -> dict[str, Any]:
        await self.update_jwks_keys()
        keys = self.jwks_keys.get("keys", None)
        if not keys:
            err_msg = f"Somethin fatal happened: 'jwks_keys' keys are missing for google {self.jwks_keys=}"
            logger.critical(err_msg)
            Oauth2AuthError(err_msg)
        try:
            success = False
            for key in keys:
                try:
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
                    success = True
                    break
                except JOSEError as exc:
                    pass
            if not success:
                err_msg = f"Google JWS keys could not validate id token: {self.jwks_keys=}"
                logger.critical(err_msg)
                raise Oauth2AuthError(err_msg)
            return data
        except Exception as exc:
            err_msg = f"Google validate id token with JWS keys: {exc}"
            logger.exception(err_msg)
            raise Oauth2AuthError(err_msg)

    # https://developers.google.com/identity/protocols/oauth2/scopes#openid_connect
    def validate_requested_scope(self, granted_scope: Union[str, list[str]]) -> tuple[bool, str]:
        missing_scope = []
        if isinstance(granted_scope, str):
            granted_scope = granted_scope.split()
        for scope in self.requested_scope():
            if scope not in granted_scope:
                if (
                    scope == "https://www.googleapis.com/auth/userinfo.email"
                    and "email" not in granted_scope
                ) or (
                    scope == "https://www.googleapis.com/auth/userinfo.profile"
                    and "profile" not in granted_scope
                ):
                    missing_scope.append(scope)
        if not missing_scope:
            return (True, "")
        return (False, " ".join(missing_scope))

    async def authorize(self, code: str, token: StateToken) -> OAuth2AuthentcatedUser:
        async with httpx.AsyncClient() as client:
            try:
                params = self.get_query_params(code, token)
                response = await client.post(str(self.token_url), params=params)
                response.raise_for_status()
            except (httpx.HTTPStatusError, httpx.RequestError) as exc:
                err_msg = f"Google auth endpoint: {exc}"
                logger.error(err_msg)
                raise Oauth2AuthError(err_msg) from exc
            except Exception as exc:
                # This exception includes status_code != 200 error
                err_msg = f"Google auth endpoint: {response.status_code=} {exc=}"
                logger.error(err_msg)
                raise Oauth2AuthError(err_msg) from exc

        try:
            auth_dict: dict = response.json()
        except Exception as exc:
            err_msg = "Google auth JSON response decode: {exc}"
            logger.exception(err_msg)
            raise Oauth2AuthError(err_msg) from exc

        for key in ("access_token", "token_type", "scope", "expires_in"):
            if key not in auth_dict:
                err_msg = f"Google auth response: missing ({key=})"
                logger.error(err_msg)
                raise Oauth2AuthError(err_msg)

        token_type: str = auth_dict.get("token_type")
        if not token_type or token_type.lower() != "bearer":
            # Sanity check
            err_msg = f"Google auth endpoint: ({token_type=}) != Bearer"
            logger.error(err_msg)
            raise Oauth2AuthError(err_msg)

        ok, missing_scope = self.validate_requested_scope(auth_dict.get("scope"))
        if not ok:
            err_msg = f"Google missing scope: ({missing_scope=})"
            logger.error(err_msg)
            raise Oauth2AuthError(err_msg)

        user_dict = {}

        # nonce parameter is present for OpenId Connect
        if token.nonce is not None:
            id_token = auth_dict.get("id_token", None)
            # This should not happen
            if id_token is None:
                err_msg = "Google auth missing 'id_token'"
                logger.critical(err_msg)
                raise Oauth2AuthError(err_msg)
            else:
                access_token = auth_dict.get("access_token")
                user_dict = await self.validate_id_token(id_token, access_token)
        if token.nonce != user_dict.get("nonce", None):
            err_msg = f"Suspcious google auth nonce mismatch: {user_dict=}"
            logger.error(err_msg)
            raise Oauth2AuthError(err_msg)

        primary_email = user_dict.get("email") or ""

        if user_dict.get("email_verified", False) is not True:
            err_msg = "Google primary email not verified"
            logger.error(err_msg)
            raise OAuth2EmailPrivdedError(err_msg)

        return self.user(user_dict, auth_dict)

    def user(self, user_dict: dict, auth_dict: dict) -> OAuth2AuthentcatedUser:
        """
        user_dict: {
            'iss': 'https://accounts.google.com',
            'azp': 'xxxxxxxxxxxx-cdtsj48dhnt87mjlbn6jlt707ls2st2p.apps.googleusercontent.com',
            'aud': 'xxxxxxxxxxxx-cdtsj48dhnt87mjlbn6jlt707ls2st2p.apps.googleusercontent.com',
            'sub': '117179329109786909885',
            'email': 'test@gmail.com',
            'email_verified': True,
            'at_hash': 'pzMAnE_HNlI_qpLHZrijtw',
            'nonce': 'jeCk1aC0XxEhOQZxuLxLXPclFiB4EVU1e4g3auV0ioXBevUP',
            'name': 'Test User',
            'picture': 'https://lh3.googleusercontent.com/a-/AOh14GhZ3sVR6Jwzx6UmP-ytYGYok-DlQ7By9oCrGz-aqA=s96-c',
            'given_name': 'Test',
            'family_name': 'User',
            'locale': 'en',
            'iat': 1615159453,
            'exp': 1615163053,
        }
        """
        for key in ("sub", "email"):
            if key not in user_dict:
                raise Oauth2AuthError(f"Missing {key=} for user info during google auth")
        full_name = user_dict.get("name", None)
        if full_name is None:
            full_name = ""
            given_name = user_dict.get("given_name", None)
            family_name = user_dict.get("family_name", None)
            if given_name is not None:
                full_name = given_name
            if family_name is not None:
                full_name = full_name + " " + family_name
            full_name = full_name.strip()

        return OAuth2AuthentcatedUser(
            email=user_dict["email"],
            full_name=full_name,
            picture=user_dict.get("picture", None),
            idp=self.idp,
            idp_userid=user_dict["sub"],
            provider_creds=auth_dict,
        )
