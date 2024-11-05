from enum import Enum, unique
from functools import lru_cache
from typing import Optional

from pydantic import BaseSettings, SecretStr, validator

USERS_TABLE = "testusers"
ADMINS_TABLE = "testadmins"
APIS_TABLE = "testapis"


@unique
class Env(str, Enum):
    DEV = "DEV"
    PRODUCTION = "PRODUCTION"


class Settings(BaseSettings):
    ENV: Env = Env.DEV

    # User setting is ignored and it always uses the default value
    PORT: int = 3001
    CORS_ENABLED: bool = True
    CORS_ORIGIN: str = "http://localhost:3000"

    # User setting is ignored and it always uses the default value
    REDIS_PORT: int = 6379
    REDIS_HOST: str = "localhost"
    REDIS_PASSWORD: Optional[SecretStr] = None
    REDIS_DATABASE_NUMBER: int = 1

    # User setting is ignored and it always uses the default value
    REDIS_METRICS_PORT: int = 6379
    REDIS_METRICS_HOST: str = "localhost"
    REDIS_METRICS_PASSWORD: Optional[SecretStr] = None
    REDIS_METRICS_DATABASE_NUMBER: int = 3

    # User setting is ignored and it always uses the default value
    POSTGRESQL_PORT: int = 5432
    POSTGRESQL_HOST: str = "localhost"
    POSTGRESQL_USER: Optional[str] = None
    POSTGRESQL_PASSWORD: Optional[SecretStr] = None
    POSTGRESQL_DATABASE: str = "titanpgdb"

    # Redirect github oauth to this athena frontend URL which will then call us
    # and complete the authorization
    GITHUB_REDIRECT_URI: str = "http://localhost:3000/auth/callback"
    GITHUB_CLIENT_ID = "624fb90a5a0ac62b1dc4"
    GITHUB_CLIENT_SECRET: SecretStr = "00cf601e207ae3d85af157495b1eeba6fc00f309"

    # Redirect google oauth to this athena frontend URL which will then call us
    # and complete the authorization.
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/auth/callback"
    GOOGLE_CLIENT_ID = "483992959077-cdtsj48dhnt57mjlbn6jlt707ls2st2p.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET: SecretStr = "HO3XmTEiUGwnfFKkuy--rEA5"

    @validator("PORT", pre=True, always=True)
    def ignore_port(cls, _):
        """Always run on default port. Ignore environement"""
        return 3001

    @validator("REDIS_PORT", "REDIS_METRICS_PORT", pre=True, always=True)
    def ignore_redis_port(cls, _):
        """Always run on default port. Ignore environement"""
        return 6379

    @validator("POSTGRESQL_PORT", pre=True, always=True)
    def ignore_postgresql_port(cls, _):
        """Always run on default port. Ignore environement"""
        return 5432

    @property
    def redis_url(self) -> str:
        # redis://localhost:6379/1
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DATABASE_NUMBER}"

    @property
    def redis_password(self) -> Optional[str]:
        secret = self.REDIS_PASSWORD
        if secret is None:
            return None
        else:
            return secret.get_secret_value()

    @property
    def redis_metrics_url(self) -> str:
        # redis://localhost:6379/3
        return f"redis://{self.REDIS_METRICS_HOST}:{self.REDIS_METRICS_PORT}/{self.REDIS_METRICS_DATABASE_NUMBER}"

    @property
    def redis_metrics_password(self) -> Optional[str]:
        secret = self.REDIS_METRICS_PASSWORD
        if secret is None:
            return None
        else:
            return secret.get_secret_value()

    @property
    def postgres_url(self) -> str:
        # postgresql://localhost:5432/dbname
        return f"postgresql://{self.POSTGRESQL_HOST}/{self.POSTGRESQL_DATABASE}"

    @property
    def postgres_password(self) -> Optional[str]:
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
