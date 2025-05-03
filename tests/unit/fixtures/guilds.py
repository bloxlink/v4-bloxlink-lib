from typing import Final
import pytest
from bloxlink_lib.models.base import GuildSerializable, RoleSerializable
from tests.unit.utils import generate_snowflake

# fixtures
from .roblox.groups import group_rolesets, GroupRolesets


@pytest.fixture()
def guild_roles(group_rolesets: GroupRolesets) -> dict[int, RoleSerializable]:
    """Test Discord roles for the Military guild."""

    new_roles: dict[int, RoleSerializable] = {}

    for i, roleset in enumerate(group_rolesets.values()):
        new_snowflake = generate_snowflake()
        new_roles[new_snowflake] = RoleSerializable(
            id=new_snowflake, name=roleset.name, position=i
        )

    return new_roles


@pytest.fixture()
def military_guild(guild_roles) -> GuildSerializable:
    """Military Roleplay server."""

    return GuildSerializable(
        id=generate_snowflake(), name="Military Roleplay Community", roles=guild_roles
    )
