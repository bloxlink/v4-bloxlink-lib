import pytest
from bloxlink_lib import GuildSerializable, SnowflakeSet, RoleSerializable, GuildBind
from .fixtures import (
    GuildRoles,
    GroupRolesets,
    MockUserData,
    MockBindScenario,
    ExpectedBindsResult,
    MockedBindScenarioResult,
    MockBadges,
    BadgeBindTestCase,
    BindTestFixtures,
    BindTestCase,
)


class TestBinds:
    """Test the logic of binds"""

    @pytest.mark.parametrize(
        "mock_bind_scenario",
        [
            MockBindScenario(
                test_cases=[
                    BindTestCase(
                        test_fixture=BindTestFixtures.GROUPS.EVERYONE_GROUP_BIND,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=True,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.MEMBER],
                    current_group_roleset=GroupRolesets.OFFICER,
                ),
            ),
            MockBindScenario(
                test_cases=[
                    BindTestCase(
                        test_fixture=BindTestFixtures.GROUPS.DYNAMIC_ROLES_GROUP_BIND,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=True,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.COMMANDER],
                    current_group_roleset=GroupRolesets.OFFICER,
                ),
            ),
            MockBindScenario(
                test_cases=[
                    BindTestCase(
                        test_fixture=BindTestFixtures.GROUPS.GUEST_GROUP_BIND,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=True,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.VERIFIED],
                    current_group_roleset=None,
                ),
            ),
            MockBindScenario(
                test_cases=[
                    BindTestCase(
                        test_fixture=BindTestFixtures.GROUPS.GUEST_GROUP_BIND,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=False,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.VERIFIED],
                    current_group_roleset=GroupRolesets.OFFICER,
                ),
            ),
            MockBindScenario(
                test_cases=[
                    BindTestCase(
                        test_fixture=BindTestFixtures.GROUPS.ROLESET_GROUP_BIND,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=True,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.VERIFIED],
                    current_group_roleset=GroupRolesets.COMMANDER,
                ),
            ),
            MockBindScenario(
                test_cases=[
                    BindTestCase(
                        test_fixture=BindTestFixtures.GROUPS.ROLESET_GROUP_BIND,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=False,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.VERIFIED],
                    current_group_roleset=GroupRolesets.MEMBER,
                ),
            ),
            MockBindScenario(
                test_cases=[
                    BindTestCase(
                        test_fixture=BindTestFixtures.GROUPS.MIN_MAX_GROUP_BIND,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=True,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.VERIFIED],
                    current_group_roleset=GroupRolesets.COMMANDER,
                ),
            ),
            MockBindScenario(
                test_cases=[
                    BindTestCase(
                        test_fixture=BindTestFixtures.GROUPS.MIN_MAX_GROUP_BIND,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=True,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.VERIFIED],
                    current_group_roleset=GroupRolesets.ADMIN,
                ),
            ),
            MockBindScenario(
                test_cases=[
                    BindTestCase(
                        test_fixture=BindTestFixtures.GROUPS.MIN_MAX_GROUP_BIND,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=False,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.VERIFIED],
                    current_group_roleset=GroupRolesets.MEMBER,
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
        """Test that a user in a group satisfies the group bind."""

        await _assert_successful_binds_results(
            mocked_bind_scenario=mock_bind_scenario,
            guild_roles=test_guild.roles,
        )

    @pytest.mark.parametrize(
        "mock_bind_scenario",
        [
            MockBindScenario(
                test_cases=[
                    BindTestCase(
                        test_fixture=BindTestFixtures.VERIFIED.VERIFIED_BIND,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=True,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.UNVERIFIED],
                    current_group_roleset=None,
                    verified=True,
                ),
            ),
            MockBindScenario(
                test_cases=[
                    BindTestCase(
                        test_fixture=BindTestFixtures.VERIFIED.VERIFIED_BIND,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=True,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.VERIFIED],
                    current_group_roleset=None,
                    verified=False,
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
                test_cases=[
                    BindTestCase(
                        test_fixture=BindTestFixtures.VERIFIED.UNVERIFIED_BIND,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=True,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[],
                    current_group_roleset=None,
                    verified=False,
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
        """Test that a user in a group satisfies the unverified bind."""

        await _assert_successful_binds_results(
            mocked_bind_scenario=mock_bind_scenario,
            guild_roles=test_guild.roles,
        )

    @pytest.mark.parametrize(
        "mock_bind_scenario",
        [
            MockBindScenario(
                test_cases=[
                    BadgeBindTestCase(
                        test_fixture=BindTestFixtures.BADGES.BADGE_BIND,
                        badge=MockBadges.VIP_BADGE,
                        discord_role=GuildRoles.OWNS_BADGE,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=True,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[],
                    owns_assets=[MockBadges.VIP_BADGE],
                    verified=True,
                ),
            ),
        ],
        indirect=True,
    )
    @pytest.mark.asyncio_concurrent(group="bind_tests")
    async def test_badge_bind(
        self,
        test_guild: GuildSerializable,
        mock_bind_scenario: MockedBindScenarioResult,
    ):
        """Test that a user in a group satisfies the badge bind."""

        await _assert_successful_binds_results(
            mocked_bind_scenario=mock_bind_scenario,
            guild_roles=test_guild.roles,
        )


async def _assert_successful_binds_results(
    mocked_bind_scenario: MockedBindScenarioResult,
    guild_roles: list[RoleSerializable],
):
    for i, bind in enumerate(mocked_bind_scenario.test_against_binds):
        expected_result = mocked_bind_scenario.expected_results[i]
        result = await bind.satisfies_for(
            roblox_user=mocked_bind_scenario.mock_user.roblox_user,
            member=mocked_bind_scenario.mock_user.discord_user,
            guild_roles=guild_roles,
        )

        assert result.successful == expected_result.expected_bind_success
        assert result.ineligible_roles == SnowflakeSet(
            expected_result.expected_remove_roles
        )
