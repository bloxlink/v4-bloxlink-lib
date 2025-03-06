from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Type definition for config values."""

    DISCORD_TOKEN: str | None = None
    BOT_RELEASE: Literal["LOCAL", "CANARY", "MAIN", "PRO"]
    #############################
    # these are optional because we can choose to use MONGO_URL or MONGO_HOST/MONGO_USER/MONGO_PASSWORD/MONGO_PORT
    MONGO_URL: str | None = None
    MONGO_HOST: str | None = None
    MONGO_PORT: int | None = 27017
    MONGO_USER: str | None = None
    MONGO_PASSWORD: str | None = None
    MONGO_CA_FILE: str | None = None
    # these are optional because we can choose to use REDIS_URL or REDIS_HOST/REDIS_PORT/REDIS_PASSWORD
    REDIS_URL: str | None = None
    REDIS_HOST: str | None = None
    REDIS_PORT: str | None = "6379"
    REDIS_PASSWORD: str | None = None
    #############################
    PROXY_URL: str | None = None
    DISCORD_PROXY_URL: str | None = None
    BOT_API: str | None = None
    BOT_API_AUTH: str | None = None
    SENTRY_DSN: str | None = None
    #############################
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    SHARD_COUNT: int = 1
    SHARDS_PER_NODE: int = 1
    #############################
    TEST_MODE: bool = False  # if true, skip database and redis connections

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def model_post_init(self, __context):
        # easier to validate with python expressions instead of attrs validators

        if self.TEST_MODE:
            return

        if self.REDIS_URL is None and (
            self.REDIS_HOST is None or self.REDIS_PORT is None
        ):
            raise ValueError(
                "REDIS_URL or REDIS_HOST/REDIS_PORT/REDIS_PASSWORD must be set"
            )

        if all([self.REDIS_HOST, self.REDIS_PORT, self.REDIS_PASSWORD, self.REDIS_URL]):
            raise ValueError(
                "REDIS_URL and REDIS_HOST/REDIS_PORT/REDIS_PASSWORD cannot both be set"
            )

        if self.MONGO_URL is None and (
            self.MONGO_HOST is None or self.MONGO_PORT is None
        ):
            raise ValueError(
                "MONGO_URL or MONGO_HOST/MONGO_PORT/MONGO_USER/MONGO_PASSWORD must be set"
            )

        if all(
            [
                self.MONGO_HOST,
                self.MONGO_PORT,
                self.MONGO_USER,
                self.MONGO_PASSWORD,
                self.MONGO_URL,
            ]
        ):
            raise ValueError(
                "MONGO_URL and MONGO_HOST/MONGO_PORT/MONGO_USER/MONGO_PASSWORD cannot both be set"
            )


CONFIG: Config = Config()
