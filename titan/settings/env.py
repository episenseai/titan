from functools import lru_cache

from pydantic import BaseSettings, SecretStr

from ..utils import ImmutBaseModel

USERS_TABLE = "testusers"
ADMINS_TABLE = "testadmins"
APIS_TABLE = "testapis"


class Settings(BaseSettings):
    PORT: int = 3001
    REDIS_PASSWORD: SecretStr = "password123"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DATABASE_NUMBER: int = 2

    POSTGRESQL_USER: str = "postgres"
    POSTGRESQL_PASSWORD: SecretStr = "password123"
    POSTGRESQL_HOST: str = "localhost"
    POSTGRESQL_PORT: int = 5432
    POSTGRESQL_DATABASE: str = "mypostgresdb"

    GITHUB_CLIENT_ID = "5ffe8fd42976c5f477e3"
    GITHUB_CLIENT_SECRET: SecretStr = "d6d6dc23b03f3b53a3d471ae02acd76c3e893ded"

    GOOGLE_CLIENT_ID = "483992959077-cdtsj48dhnt87mjlbn6jlt707ls2st2p.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET: SecretStr = "WmUcqKFLcbiYSqghIIuUi4Hb"

    @property
    def redis_url(self) -> str:
        # redis://localhost:6379/0
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DATABASE_NUMBER}"

    @property
    def postgres_url(self) -> str:
        # postgresql://localhost:5432/dbname
        return f"postgresql://{self.POSTGRESQL_HOST}/{self.POSTGRESQL_DATABASE}"

    class Config:
        env_prefix = "TITAN_"
        case_sensitive = True


@lru_cache
def env() -> Settings:
    return Settings()
