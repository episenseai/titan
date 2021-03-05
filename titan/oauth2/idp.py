from enum import Enum


class IdP(str, Enum):
    episense = "episense"
    github = "github"
    google = "google"
