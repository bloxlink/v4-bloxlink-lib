import pytest
from bloxlink_lib import GuildSerializable, SnowflakeSet, find, RoleSerializable
from .fixtures import (
    GuildRoles,
    GroupRolesets,
    MockUserData,
    MockBindScenario,
    ExpectedBinds,
    MockedBindScenarioResult,
)


class TestBinds:
    """Test the logic of binds"""

    @pytest.mark.parametrize(
        "mock_bind_scenario",
        [
            MockBindScenario(
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.MEMBER],
                    current_group_roleset=GroupRolesets.OFFICER,
                ),
                test_against_bind_fixtures=["everyone_group_bind"],
                expected_binds=ExpectedBinds(
                    expected_bind_success=True,
                ),
            ),
            MockBindScenario(
                test_against_bind_fixtures=["dynamic_roles_group_bind"],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.COMMANDER],
                    current_group_roleset=GroupRolesets.OFFICER,
                ),
                expected_binds=ExpectedBinds(
                    expected_remove_roles=[GuildRoles.COMMANDER],
                    expected_bind_success=True,
                ),
            ),
            MockBindScenario(
                test_against_bind_fixtures=["guest_group_bind"],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.VERIFIED],
                    current_group_roleset=None,
                ),
                expected_binds=ExpectedBinds(
                    expected_bind_success=True,
                ),
            ),
            MockBindScenario(
                test_against_bind_fixtures=["guest_group_bind"],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.VERIFIED],
                    current_group_roleset=GroupRolesets.OFFICER,
                ),
                expected_binds=ExpectedBinds(
                    expected_bind_success=False,
                ),
            ),
            MockBindScenario(
                test_against_bind_fixtures=["roleset_group_bind"],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.VERIFIED],
                    current_group_roleset=GroupRolesets.COMMANDER,
                ),
                expected_binds=ExpectedBinds(
                    expected_bind_success=True,
                ),
            ),
            MockBindScenario(
                test_against_bind_fixtures=["roleset_group_bind"],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.VERIFIED],
                    current_group_roleset=GroupRolesets.MEMBER,
                ),
                expected_binds=ExpectedBinds(
                    expected_bind_success=False,
                ),
            ),
            MockBindScenario(
                test_against_bind_fixtures=["min_max_group_bind"],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.VERIFIED],
                    current_group_roleset=GroupRolesets.COMMANDER,
                ),
                expected_binds=ExpectedBinds(
                    expected_bind_success=True,
                ),
            ),
            MockBindScenario(
                test_against_bind_fixtures=["min_max_group_bind"],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.VERIFIED],
                    current_group_roleset=GroupRolesets.ADMIN,
                ),
                expected_binds=ExpectedBinds(
                    expected_bind_success=True,
                ),
            ),
            MockBindScenario(
                test_against_bind_fixtures=["min_max_group_bind"],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.VERIFIED],
                    current_group_roleset=GroupRolesets.MEMBER,
                ),
                expected_binds=ExpectedBinds(
                    expected_bind_success=False,
                ),
            ),
        ],
        indirect=True,
    )
    @pytest.mark.asyncio_concurrent(group="bind_tests")
    async def test_group_binds(
        self,
        test_guild: GuildSerializable,
        mock_bind_scenario: MockedBindScenarioResult,
    ):
        """Test that a user in a group with everyone=True binding satisfies the condition."""

        await _assert_successful_binds_results(
            mocked_bind_scenario=mock_bind_scenario,
            guild_roles=test_guild.roles,
        )

    @pytest.mark.parametrize(
        "mock_bind_scenario",
        [
            MockBindScenario(
                test_against_bind_fixtures=["verified_bind"],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.UNVERIFIED],
                    current_group_roleset=None,
                    verified=True,
                ),
                expected_binds=ExpectedBinds(
                    expected_bind_success=True,
                ),
            ),
            MockBindScenario(
                test_against_bind_fixtures=["verified_bind"],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.VERIFIED],
                    current_group_roleset=None,
                    verified=False,
                ),
                expected_binds=ExpectedBinds(
                    expected_remove_roles=[GuildRoles.VERIFIED],
                    expected_bind_success=False,
                ),
            ),
        ],
        indirect=True,
    )
    @pytest.mark.asyncio_concurrent(group="bind_tests")
    async def test_verified_bind(
        self,
        test_guild: GuildSerializable,
        mock_bind_scenario: MockedBindScenarioResult,
    ):
        """Test that a verified user satisfies the verified bind."""

        await _assert_successful_binds_results(
            mocked_bind_scenario=mock_bind_scenario,
            guild_roles=test_guild.roles,
        )

    @pytest.mark.parametrize(
        "mock_bind_scenario",
        [
            MockBindScenario(
                test_against_bind_fixtures=["unverified_bind"],
                mock_user=MockUserData(
                    current_discord_roles=[],
                    current_group_roleset=None,
                    verified=False,
                ),
                expected_binds=ExpectedBinds(
                    expected_bind_success=True,
                ),
            ),
        ],
        indirect=True,
    )
    @pytest.mark.asyncio_concurrent(group="bind_tests")
    async def test_unverified_bind(
        self,
        test_guild: GuildSerializable,
        mock_bind_scenario: MockedBindScenarioResult,
    ):
        """Test that a user in a group with everyone=True binding satisfies the condition."""

        await _assert_successful_binds_results(
            mocked_bind_scenario=mock_bind_scenario,
            guild_roles=test_guild.roles,
        )


async def _assert_successful_binds_results(
    mocked_bind_scenario: MockedBindScenarioResult,
    guild_roles: list[RoleSerializable],
):
    expected_remove_roles = (
        mocked_bind_scenario.expected_binds.expected_remove_roles or []
    )
    expected_bind_success = mocked_bind_scenario.expected_binds.expected_bind_success
    expected_additional_roles = []
    expected_missing_roles = []

    for bind in mocked_bind_scenario.test_against_bind_fixtures:
        result = await bind.satisfies_for(
            roblox_user=mocked_bind_scenario.mock_user.roblox_user,
            member=mocked_bind_scenario.mock_user.discord_user,
            guild_roles=guild_roles,
        )

        assert result.successful == expected_bind_success
        assert result.additional_roles == SnowflakeSet(expected_additional_roles)
        assert result.missing_roles == SnowflakeSet(expected_missing_roles)
        assert result.ineligible_roles == SnowflakeSet(expected_remove_roles)
