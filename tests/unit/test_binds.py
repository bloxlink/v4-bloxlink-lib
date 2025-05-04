import pytest
from bloxlink_lib import GuildSerializable
from bloxlink_lib.models import binds

# fixtures
from .fixtures.binds import entire_group_bind
from .fixtures.guilds import test_guild, guild_roles, GuildRoles
from .fixtures.groups import GroupRolesets
from .fixtures.users import test_group_member, MockUser, MockUserData, mock_user


class TestBinds:
    """Test the logic of binds"""

    @pytest.mark.parametrize(
        "mock_user",
        [
            MockUserData(
                current_discord_roles=[GuildRoles.MEMBER],
                current_group_roleset=GroupRolesets.RANK_1,
            )
        ],
        indirect=True,
    )
    @pytest.mark.asyncio_concurrent(group="bind_tests_entire_group_bind")
    async def test_entire_group_bind(
        self,
        entire_group_bind: binds.GuildBind,
        test_guild: GuildSerializable,
        mock_user: MockUser,
    ):
        """Test that a user in a group with everyone=True binding receives the roles."""

        result = await entire_group_bind.satisfies_for(
            roblox_user=mock_user.roblox_user,
            member=mock_user.discord_user,
            guild_roles=test_guild.roles,
        )

        assert result.successful, "The user must satisfy this bind condition"
