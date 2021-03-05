from enum import Enum
from typing import Optional

from pydantic import AnyHttpUrl

from ..models import ImmutBaseModel


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
