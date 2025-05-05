from enum import Enum
import pytest
from bloxlink_lib import GuildSerializable, RoleSerializable
from tests.unit.utils import generate_snowflake

__all__ = ["GuildRoles", "GuildRolesType", "guild_roles", "test_guild"]


class GuildRoles(Enum):
    """The Discord roles in the test server"""

    VERIFIED = "Verified"
    UNVERIFIED = "Unverified"
    NOT_IN_GROUP = "Not in Group"
    MEMBER = "Member"
    OFFICER = "Officer"
    COMMANDER = "Commander"
    ADMIN = "Leader"

    def __str__(self):
        return self.value


GuildRolesType = dict[int, RoleSerializable]


@pytest.fixture(scope="function")
def guild_roles() -> GuildRolesType:
    """Test Discord roles for the test Discord server."""

    new_roles: dict[int, RoleSerializable] = {}

    for i, discord_role in enumerate(GuildRoles):
        new_snowflake = generate_snowflake()
        new_roles[new_snowflake] = RoleSerializable(
            id=new_snowflake, name=discord_role.value, position=i
        )

    return new_roles


@pytest.fixture(scope="function")
def test_guild(guild_roles: GuildRolesType) -> GuildSerializable:
    """Test Discord server."""

    return GuildSerializable(
        id=generate_snowflake(), name="Military Roleplay Community", roles=guild_roles
    )
