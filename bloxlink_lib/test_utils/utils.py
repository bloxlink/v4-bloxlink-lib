from snowflake import SnowflakeGenerator

snowflake_generator = SnowflakeGenerator(1)


__all__ = [
    "generate_snowflake",
]


def generate_snowflake() -> int:
    """Utility to generate Twitter Snowflakes"""

    return next(snowflake_generator)
