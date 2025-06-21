import pytest
from snowflake import SnowflakeGenerator

from bloxlink_lib import RoleSerializable, find

snowflake_generator = SnowflakeGenerator(1)


__all__ = [
    "generate_snowflake",
]


def generate_snowflake() -> int:
    """Utility to generate Twitter Snowflakes"""

    return next(snowflake_generator)
