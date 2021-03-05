from abc import ABC, abstractmethod, abstractstaticmethod
from typing import Any, Dict, Optional, Tuple, Type, Union

from pydantic import AnyHttpUrl, SecretStr

from ..models import ImmutBaseModel
from .idp import IdP
from .state import StateToken


class OAuth2TokenGrant(ImmutBaseModel):
    access_token: str
    token_type: str
    expires_in: Optional[int] = None
    scope: Optional[str] = None
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None


class OAuth2Provider(ImmutBaseModel):
    # authorize with the identity provider, return 'code' and 'state'
    auth_url: AnyHttpUrl
    # get the access_token and/or refresh_token and/or id_token
    token_url: AnyHttpUrl
    # optional user info endpoint, ex. present in case of github
    user_url: Optional[AnyHttpUrl] = None


class OAuth2ClientBase(OAuth2Provider):
    # get this id from the provider
    client_id: str
    # requested scope from the provider during authentication
    scope: str
    # callback url: auth_url redirects here with 'code' and 'state'
    redirect_uri: AnyHttpUrl


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
    def create_auth_url(self, token: StateToken) -> str:
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
    def get_query_params(self, code: str, state: str) -> str:
        pass

    @abstractmethod
    async def authorize(self, code: str, state: str) -> Tuple[OAuth2TokenGrant, Dict[str, Any]]:
        """
        Exchange code for access_token and/or id_token
        Return value: (token_grant, user_dict)
        """
        pass

    @abstractmethod
    def get_email_str(self, user_dict: Dict[str, Any]) -> Optional[str]:
        pass

    @abstractmethod
    def get_provider_id(self, user_dict: Dict[str, Any]) -> Optional[str]:
        pass


class Oauth2ClientRegistry:
    def __init__(self, registry_class: Union[Type[OAuth2LoginClient], Type[OAuth2AuthClient]]):
        assert registry_class in [OAuth2LoginClient, OAuth2AuthClient]
        self._registry_class = registry_class
        self._registry = {}

    def add(self, client: Union[OAuth2LoginClient, OAuth2AuthClient]):
        if isinstance(client, self._registry_class):
            self._registry[client.idp] = client
        else:
            RuntimeError("Can not add different classes to same registry")

    def get(self, idp: IdP):
        return self._registry[idp]
