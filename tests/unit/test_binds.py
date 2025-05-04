import pytest
from bloxlink_lib import GuildSerializable, SnowflakeSet
from bloxlink_lib.models.base.serializable import RoleSerializable
from .fixtures import GuildRoles, GroupRolesets, MockUser, MockUserData


class TestBinds:
    """Test the logic of binds"""

    @pytest.mark.parametrize(
        "mock_verified_user",
        [
            MockUserData(
                current_discord_roles=[GuildRoles.MEMBER],
                current_group_roleset=GroupRolesets.RANK_1,
                test_against_bind_fixtures=["everyone_group_bind"],
            ),
            MockUserData(
                current_discord_roles=[GuildRoles.RANK_2],
                current_group_roleset=GroupRolesets.RANK_1,
                expected_removed_roles=[GuildRoles.RANK_2],
                test_against_bind_fixtures=["dynamic_roles_group_bind"],
            ),
            MockUserData(
                current_discord_roles=[GuildRoles.VERIFIED],
                current_group_roleset=None,
                test_against_bind_fixtures=["guest_group_bind"],
            ),
        ],
        indirect=True,
    )
    @pytest.mark.asyncio_concurrent(group="bind_tests_group_binds")
    async def test_group_binds(
        self,
        test_guild: GuildSerializable,
        mock_verified_user: MockUser,
    ):
        """Test that a user in a group with everyone=True binding satisfies the condition."""

        await _assert_successful_binds_results(
            mocked_user=mock_verified_user,
            guild_roles=test_guild.roles,
        )

    @pytest.mark.parametrize(
        "mock_verified_user",
        [
            MockUserData(
                current_discord_roles=[GuildRoles.UNVERIFIED],
                current_group_roleset=None,
                test_against_bind_fixtures=["verified_bind"],
            )
        ],
        indirect=True,
    )
    @pytest.mark.asyncio_concurrent(group="bind_tests_verified_binds")
    async def test_verified_bind(
        self,
        test_guild: GuildSerializable,
        mock_verified_user: MockUser,
    ):
        """Test that a verified user satisfies the verified bind."""

        await _assert_successful_binds_results(
            mocked_user=mock_verified_user,
            guild_roles=test_guild.roles,
            expected_remove_roles=mock_verified_user.expected_removed_roles,
        )

    @pytest.mark.parametrize(
        "mock_unverified_user",
        [
            MockUserData(
                current_discord_roles=[],
                current_group_roleset=None,
                test_against_bind_fixtures=["unverified_bind"],
            ),
            MockUserData(
                current_discord_roles=[GuildRoles.RANK_1],
                expected_removed_roles=[GuildRoles.RANK_1],
                current_group_roleset=None,
                test_against_bind_fixtures=["unverified_bind"],
            ),
        ],
        indirect=True,
    )
    @pytest.mark.asyncio_concurrent(group="bind_tests_unverified_bind")
    async def test_unverified_bind(
        self,
        test_guild: GuildSerializable,
        mock_unverified_user: MockUser,
    ):
        """Test that a user in a group with everyone=True binding satisfies the condition."""

        await _assert_successful_binds_results(
            mocked_user=mock_unverified_user,
            guild_roles=test_guild.roles,
        )


async def _assert_successful_binds_results(
    mocked_user: MockUser,
    guild_roles: list[RoleSerializable],
    expected_additional_roles: list[int] | None = None,
    expected_missing_roles: list[int] | None = None,
    expected_remove_roles: list[int] | None = None,
):
    expected_additional_roles = expected_additional_roles or []
    expected_missing_roles = expected_missing_roles or []
    expected_ineligible_roles = expected_remove_roles or []

    for bind in mocked_user.test_against_bind_fixtures:
        result = await bind.satisfies_for(
            roblox_user=mocked_user.roblox_user,
            member=mocked_user.discord_user,
            guild_roles=guild_roles,
        )

        assert result.successful, "The user must satisfy this bind condition"
        assert result.additional_roles == SnowflakeSet(expected_additional_roles)
        assert result.missing_roles == SnowflakeSet(expected_missing_roles)
        assert result.ineligible_roles == SnowflakeSet(expected_ineligible_roles)
