import pytest
from bloxlink_lib import GuildSerializable, BindCalculationResult
from bloxlink_lib.models import binds
from .fixtures import GuildRoles, GroupRolesets, MockUser, MockUserData


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
        """Test that a user in a group with everyone=True binding satisfies the condition."""

        result = await entire_group_bind.satisfies_for(
            roblox_user=mock_user.roblox_user,
            member=mock_user.discord_user,
            guild_roles=test_guild.roles,
        )

        _assert_successful_bind_result(result)


def _assert_successful_bind_result(result: BindCalculationResult):
    assert result.successful, "The user must satisfy this bind condition"
    assert (
        not result.additional_roles
    ), "The user should not receive any additional roles"
    assert not result.missing_roles, "The guild should not be missing any roles"
    assert (
        not result.ineligible_roles
    ), "The user should not be ineligible for any roles"
