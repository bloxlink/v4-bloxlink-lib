import pytest
from bloxlink_lib.models.base import GuildSerializable, RoleSerializable


@pytest.fixture
def test_guild_1() -> GuildSerializable:
    """Test Guild model."""

    return GuildSerializable(
        id=7323844246044188672,
        name="My awesome server",
        roles={
            1: RoleSerializable(
                id=1,
                name="Admin",
                color=0xFF0000,
                is_hoisted=True,
                position=1,
                permissions=0,
                is_managed=False,
                is_mentionable=True,
            )
        },
    )


@pytest.fixture
def test_role_1() -> GuildSerializable:
    """Test Guild model."""

    return RoleSerializable(
        id=987654321,
        name="My awesome server",
        roles={
            1: RoleSerializable(
                id=1,
                name="Admin",
                color=0xFF0000,
                is_hoisted=True,
                position=1,
                permissions=0,
                is_managed=False,
                is_mentionable=True,
            )
        },
    )
