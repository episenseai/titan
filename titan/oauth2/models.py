from abc import ABC, abstractmethod, abstractstaticmethod
from typing import Any, Optional, Union

from pydantic import AnyHttpUrl, SecretStr

from ..models import ImmutBaseModel
from .idp import IdP
from .state import StateToken


class OAuth2AuthentcatedCreds(ImmutBaseModel):
    access_token: str
    token_type: str
    expires_in: Optional[int] = None
    scope: Union[str, list[str]]
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None


class OAuth2AuthentcatedUser(ImmutBaseModel):
    email: str
    full_name: Optional[str] = None
    picture: Optional[str] = None
    idp: IdP
    idp_guid: str
    idp_username: Optional[str] = None
    provider_creds: Optional[OAuth2AuthentcatedCreds] = None


class OAuth2Provider(ImmutBaseModel):
    # authorize with the identity provider, return 'code' and 'state'
    auth_url: AnyHttpUrl
    # get the access_token and/or refresh_token and/or id_token
    token_url: AnyHttpUrl
    # url where to find the public keys of the provider to verify the token
    jwks_uri: Optional[AnyHttpUrl] = None
    # public keys of the provider
    jwks_keys: dict[str, Any] = {}


class OAuth2ClientBase(OAuth2Provider):
    # get this id from the provider
    client_id: str
    # requested scope from the provider during authentication
    scope: Union[str, list[str]]
    # callback url: auth_url redirects here with 'code' and 'state'
    redirect_uri: AnyHttpUrl
    # If it's a JWT token, then it represents 'iss' claim of the
    # received token
    iss: Optional[str] = None

    def requested_scope(self) -> list[str]:
        if isinstance(self.scope, list):
            return self.scope.copy()
        return self.scope.split().copy()


class OAuth2LoginClient(OAuth2ClientBase, ABC):
    @abstractstaticmethod
    def new(
        client_id: str,
        scope: str,
        redirect_uri: Union[AnyHttpUrl, str],
    ) -> "OAuth2LoginClient":
        """
        Builder method to create an instance of the class
        """
        pass

    @property
    @abstractmethod
    def idp(self) -> IdP:
        pass

    @abstractmethod
    def get_query_params(self, token: StateToken, refresh_token: bool) -> dict[str, Any]:
        pass

    @abstractmethod
    def get_urlencoded_query_params(self, token: StateToken, refresh_token: bool) -> str:
        pass

    @abstractmethod
    def create_auth_url(self, token: StateToken, refresh_token: bool) -> str:
        pass


class OAuth2AuthClient(OAuth2ClientBase, ABC):
    # use only with the token_url endpoint
    client_secret: SecretStr

    @abstractstaticmethod
    def new(
        client_id: str,
        scope: str,
        redirect_uri: Union[AnyHttpUrl, str],
        client_secret: Union[SecretStr, str],
    ) -> "OAuth2AuthClient":
        """
        Builder method to create an instance of the class
        """
        pass

    @property
    @abstractmethod
    def idp(self) -> IdP:
        pass

    @abstractmethod
    def get_query_params(self, code: str, token: StateToken) -> dict[str, Any]:
        pass

    @abstractmethod
    def get_urlencoded_query_params(self, code: str, token: StateToken) -> str:
        pass

    @abstractmethod
    def validate_requested_scope(self, granted_scope: Union[str, list[str]]) -> bool:
        pass

    @abstractmethod
    async def authorize(self, code: str, token: StateToken) -> OAuth2AuthentcatedUser:
        """
        Exchange code for access_token and/or id_token
        Return value: (token_grant, user_dict)
        """
        pass

    @abstractmethod
    def user(self, user_dict: dict, auth_dict: dict) -> OAuth2AuthentcatedUser:
        pass
