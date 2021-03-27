from enum import Enum


class IdentityProvider(str, Enum):
    github = "github"
    google = "google"
