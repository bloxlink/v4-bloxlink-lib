import pytest
from bloxlink_lib import GuildSerializable
from bloxlink_lib.models import binds

# fixtures
from .fixtures.binds import entire_group_bind
from .fixtures.guilds import military_guild, guild_roles
from .fixtures.users import test_military_member, User


class TestBinds:
    """Test the logic of binds"""

    @pytest.mark.asyncio_concurrent(group="bind_tests_entire_group_bind")
    async def test_entire_group_bind(
        self,
        entire_group_bind: binds.GuildBind,
        military_guild: GuildSerializable,
        test_military_member: User,
    ):
        """Test that a user in a group with everyone=True binding receives the roles."""

        result = await entire_group_bind.satisfies_for(
            roblox_user=test_military_member.roblox_user,
            member=test_military_member.discord_user,
            guild_roles=military_guild.ro,
        )

        print(result)

        assert 1 == 2  # FIXME debugging
