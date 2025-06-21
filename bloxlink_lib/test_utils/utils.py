import pytest
from snowflake import SnowflakeGenerator

from bloxlink_lib import RoleSerializable, find

snowflake_generator = SnowflakeGenerator(1)


__all__ = [
    "generate_snowflake",
    "find_discord_roles",
]


def generate_snowflake() -> int:
    """Utility to generate Twitter Snowflakes"""

    return next(snowflake_generator)


@pytest.fixture()
def find_discord_roles(guild_roles: "GuildRolesType") -> list[RoleSerializable]:
    """Retrieve the Discord roles from the GuildRoles enum"""

    from bloxlink_lib.test_utils.fixtures.guilds import GuildRoles

    def _find_discord_roles(*role_enums: GuildRoles) -> list[RoleSerializable]:
        return [
            find(lambda r: r.name == role_enum.value, guild_roles.values())
            for role_enum in role_enums
        ]

    return _find_discord_roles
