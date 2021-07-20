from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, SecretStr

from ..utils import ImmutBaseModel

USERS_TABLE = "testusers"
ADMINS_TABLE = "testadmins"
APIS_TABLE = "testapis"


class Settings(BaseSettings):
    PORT: int = 3001
    REDIS_PASSWORD: SecretStr = ""  # "password123"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DATABASE_NUMBER: int = 2

    POSTGRESQL_USER: Optional[str] = None  # "postgres"
    POSTGRESQL_PASSWORD: Optional[SecretStr] = None  # "password123"
    POSTGRESQL_HOST: str = "localhost"
    POSTGRESQL_PORT: int = 5432
    POSTGRESQL_DATABASE: str = "titanpgdb"  # "mypostgresdb"

    GITHUB_CLIENT_ID = "624fb90a5a0ac62b1db4"
    GITHUB_CLIENT_SECRET: SecretStr = "00cf601e207ae3d85af157495b1eeba6fc00f509"
    GITHUB_REDIRECT_URI: str = "http://localhost:3000/auth/callback"

    GOOGLE_CLIENT_ID = "483992959077-cdtsj48dhnt87mjlbn6jlt707ls2st2p.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET: SecretStr = "HO3XmTEiUGwnfFKkuy--rEA4"
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/auth/callback"

    @property
    def redis_url(self) -> str:
        # redis://localhost:6379/0
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DATABASE_NUMBER}"

    @property
    def postgres_url(self) -> str:
        # postgresql://localhost:5432/dbname
        return f"postgresql://{self.POSTGRESQL_HOST}/{self.POSTGRESQL_DATABASE}"

    @property
    def postgres_pasword(self) -> Optional[str]:
        secret = self.POSTGRESQL_PASSWORD
        if secret is None:
            return None
        else:
            return secret.get_secret_value()

    class Config:
        env_prefix = "TITAN_"
        case_sensitive = True


@lru_cache
def env() -> Settings:
    return Settings()
