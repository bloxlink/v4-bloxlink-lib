import logging
from typing import Final, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_METRICS_PORT: Final[int] = 9090


class BaseConfig(BaseSettings):
    """Type definition for config values."""

    #############################
    # GENERAL SETTINGS
    #############################
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    SENTRY_DSN: str | None = None
    NODE_LOCK_TTL: int = 600
    #############################

    # METRICS AND LOGGING
    #############################
    METRICS_HOST: str = "0.0.0.0"
    METRICS_PORT: int = DEFAULT_METRICS_PORT
    METRICS_ENABLED: bool = True
    #############################
    # BOT SETTINGS
    #############################
    BOT_TOKEN: str | None = None
    BOT_RELEASE: Literal["LOCAL", "CANARY", "MAIN", "PRO"] | None = None

    BOT_API: str | None = None
    BOT_API_AUTH: str | None = None

    PROXY_URL: str | None = None
    DISCORD_PROXY_URL: str | None = None

    SHARD_COUNT: int | None = None
    SHARDS_PER_NODE: int | None = None
    #############################
    # DATABASE SETTINGS
    #############################
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
    # OPTIONAL BLOXLINK VERIFICATION SETTINGS
    #############################
    STAGING_USE_FALLBACK_VERIFICATION_API: bool | None = (
        False  # if true, use the production verification API if a user is not verified
    )
    BLOXLINK_PUBLIC_API_KEY: str | None = None
    #############################
    # TESTING SETTINGS
    #############################
    SKIP_DB_VALIDATION: bool = False

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    def model_post_init(self, __context):
        if getattr(self, "PORT", None) == DEFAULT_METRICS_PORT:
            raise ValueError(
                f"PORT cannot be set to the default metrics port ({DEFAULT_METRICS_PORT}). Please set a different port."
            )

        if self.SKIP_DB_VALIDATION:
            logging.info("SKIP_DB_VALIDATION is enabled, skipping database validation")
            return

        if self.REDIS_URL is None and (
            self.REDIS_HOST is None or self.REDIS_PORT is None
        ):
            raise ValueError(
                "REDIS_URL or REDIS_HOST/REDIS_PORT/REDIS_PASSWORD must be set"
            )

        if self.REDIS_URL and self.REDIS_HOST:
            raise ValueError(
                "REDIS_URL and REDIS_HOST/REDIS_PORT/REDIS_PASSWORD cannot both be set"
            )

        if self.MONGO_URL is None and (
            self.MONGO_HOST is None or self.MONGO_PORT is None
        ):
            raise ValueError(
                "MONGO_URL or MONGO_HOST/MONGO_PORT/MONGO_USER/MONGO_PASSWORD must be set"
            )

        if self.MONGO_URL and self.MONGO_HOST:
            raise ValueError(
                "MONGO_URL and MONGO_HOST/MONGO_PORT/MONGO_USER/MONGO_PASSWORD cannot both be set"
            )


CONFIG = BaseConfig()
