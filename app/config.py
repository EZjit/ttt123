from functools import lru_cache
from os import path
from sys import argv

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # app config
    title: str = "International Delivery Service"
    app_version: str = "0.1.0"
    api_version: int = Field(default=1)
    debug: bool = Field(default=True)
    init_db: bool = Field(default=False)
    # rabbit
    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    queue_name: str = "delivery"

    # db
    db_host: str = "db"
    mysql_database: str = "delivery"
    mysql_user: str = "user"
    mysql_password: str = "password"
    # redis
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    secret_key: str = "your-secret-key"
    https_only: bool = False

    workers: int = 1

    testing_mode: bool = path.basename(argv[0]) in {"pytest", "py.test"}
    model_config = SettingsConfigDict(
        env_file="../config/.env",
        case_sensitive=False,
    )


@lru_cache()
def get_settings():
    return Settings()