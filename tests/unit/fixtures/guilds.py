from enum import Enum
import pytest
from bloxlink_lib.models.base import GuildSerializable, RoleSerializable
from tests.unit.utils import generate_snowflake


class GuildRoles(Enum):
    """The Discord roles in the test server"""

    MEMBER = "Member"
    RANK_1 = "Officer"
    RANK_2 = "Commander"
    ADMIN = "Leader"

    def __str__(self):
        return self.value


@pytest.fixture(scope="module")
def guild_roles() -> dict[int, RoleSerializable]:
    """Test Discord roles for the test Discord server."""

    new_roles: dict[int, RoleSerializable] = {}

    for i, discord_role in enumerate(GuildRoles):
        new_snowflake = generate_snowflake()
        new_roles[new_snowflake] = RoleSerializable(
            id=new_snowflake, name=discord_role.value, position=i
        )

    return new_roles


@pytest.fixture(scope="module")
def test_guild(guild_roles) -> GuildSerializable:
    """Test Discord server."""

    return GuildSerializable(
        id=generate_snowflake(), name="Military Roleplay Community", roles=guild_roles
    )
