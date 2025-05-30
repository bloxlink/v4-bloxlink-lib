from enum import Enum
import pytest
from bloxlink_lib import GuildSerializable, RoleSerializable
from bloxlink_lib.test_utils.mockers import mock_guild, mock_guild_roles

__all__ = ["GuildRoles", "GuildRolesType", "guild_roles", "test_guild"]


class GuildRoles(Enum):
    """The Discord roles in the test server"""

    VERIFIED = "Verified"  # Verified role
    UNVERIFIED = "Unverified"  # Unverified role
    NOT_IN_GROUP = "Not in Group"  # Group role
    OWNS_BADGE = "Owns Badge"  # Badge role
    OWNS_GAMEPASS = "Owns Gamepass"  # Gamepass role
    OWNS_CATALOG_ITEM = "Owns Catalog Item"  # Catalog Item role
    MEMBER = "Member"  # Group role
    OFFICER = "Officer"  # Group role
    COMMANDER = "Commander"  # Group role
    ADMIN = "Leader"  # Group role

    def __str__(self):
        return self.value


GuildRolesType = dict[int, RoleSerializable]


@pytest.fixture()
def guild_roles() -> GuildRolesType:
    """Test Discord roles for the test Discord server."""

    return mock_guild_roles(role_names=[r.value for r in GuildRoles])


@pytest.fixture()
def test_guild(guild_roles: GuildRolesType) -> GuildSerializable:
    """Test Discord server."""

    return mock_guild(role_names=[r.name for r in guild_roles.values()])
