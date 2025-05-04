import pytest
from bloxlink_lib import GuildSerializable
from bloxlink_lib.models import binds

# fixtures
from .fixtures.binds import entire_group_bind
from .fixtures.guilds import test_guild, guild_roles
from .fixtures.users import test_group_member, MockUser


class TestBinds:
    """Test the logic of binds"""

    @pytest.mark.parametrize("entire_group_bind", [["var1", "var2"]], indirect=True)
    @pytest.mark.asyncio_concurrent(group="bind_tests_entire_group_bind")
    async def test_entire_group_bind(
        self,
        entire_group_bind: binds.GuildBind,
        test_guild: GuildSerializable,
        test_group_member: MockUser,
    ):
        """Test that a user in a group with everyone=True binding receives the roles."""

        result = await entire_group_bind.satisfies_for(
            roblox_user=test_group_member.roblox_user,
            member=test_group_member.discord_user,
            guild_roles=test_guild.roles,
        )

        print(result)

        assert 1 == 2  # FIXME debugging
