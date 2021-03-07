from enum import Enum


class IdP(str, Enum):
    github = "github"
    google = "google"
