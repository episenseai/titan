import redis
from typing import Optional
from .logger import logger


class MetricsDB:
    def __init__(
        self, redis_host: str, redis_port: int, redis_password: Optional[str], redis_db: int
    ):
        self.redis = redis.Redis(
            host=redis_host, port=redis_port, password=redis_password, db=redis_db
        )
        logger.info("conected to redis metrics db")
