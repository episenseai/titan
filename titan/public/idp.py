from typing import Dict, Optional, Tuple, Any, Type, Union
from ..model import ImmutBaseModel
from pydantic import AnyHttpUrl
from enum import Enum
from abc import ABC, abstractmethod


class IdP(str, Enum):
    episense = "episense"
    github = "github"
    google = "google"


class OAuth2Provider(ImmutBaseModel):
    auth_url: AnyHttpUrl
    token_url: AnyHttpUrl


class OAuth2TokenGrant(ImmutBaseModel):
    access_token: str
    token_type: str
    expires_in: Optional[int] = None
    scope: Optional[str] = None
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None


class OAuth2LoginClient(ABC):
    @property
    @abstractmethod
    def idp(self) -> IdP:
        pass

    @abstractmethod
    def create_auth_url(self) -> str:
        pass


class OAuth2AuthClient(ABC):
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
