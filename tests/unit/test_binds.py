import pytest
from bloxlink_lib import GuildSerializable, SnowflakeSet, RoleSerializable
from bloxlink_lib.models.binds import GuildBind, BindCriteria, GroupBindData, BindData
from bloxlink_lib.test_utils.fixtures import (
    GuildRoles,
    GroupRolesets,
    MockAssets,
    AssetTypes,
    BindTestFixtures,
)
from .fixtures import (
    MockBindScenario,
    ExpectedBindsResult,
    MockedBindScenarioResult,
    AssetBindTestCase,
    BindTestCase,
)
from bloxlink_lib.test_utils.mockers import MockUserData

pytestmark = pytest.mark.binds


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
        """Test group bind logic"""

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
                            expected_bind_success=False,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[GuildRoles.VERIFIED],
                    current_group_roleset=None,
                    verified=False,
                ),
            ),
            MockBindScenario(
                test_cases=[
                    BindTestCase(
                        test_fixture=BindTestFixtures.VERIFIED.VERIFIED_BIND,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=False,
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
        """Test verified bind logic"""

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
        """Test unverified bind logic"""

        await _assert_successful_binds_results(
            mocked_bind_scenario=mock_bind_scenario,
            guild_roles=test_guild.roles,
        )

    @pytest.mark.parametrize(
        "mock_bind_scenario",
        [
            MockBindScenario(
                test_cases=[
                    AssetBindTestCase(
                        test_fixture=BindTestFixtures.ASSETS.ASSET_BIND,
                        asset=MockAssets.VIP,
                        asset_type=AssetTypes.BADGE,
                        discord_role=GuildRoles.OWNS_BADGE,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=True,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[],
                    owns_assets=[MockAssets.VIP],
                    verified=True,
                ),
            ),
            MockBindScenario(
                test_cases=[
                    AssetBindTestCase(
                        test_fixture=BindTestFixtures.ASSETS.ASSET_BIND,
                        asset=MockAssets.DONATOR,
                        asset_type=AssetTypes.BADGE,
                        discord_role=GuildRoles.OWNS_BADGE,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=False,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[],
                    owns_assets=[],
                    verified=True,
                ),
            ),
            MockBindScenario(
                test_cases=[
                    AssetBindTestCase(
                        test_fixture=BindTestFixtures.ASSETS.ASSET_BIND,
                        asset=MockAssets.VIP,
                        asset_type=AssetTypes.GAMEPASS,
                        discord_role=GuildRoles.OWNS_GAMEPASS,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=True,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[],
                    owns_assets=[MockAssets.VIP],
                    verified=True,
                ),
            ),
            MockBindScenario(
                test_cases=[
                    AssetBindTestCase(
                        test_fixture=BindTestFixtures.ASSETS.ASSET_BIND,
                        asset=MockAssets.VIP,
                        asset_type=AssetTypes.GAMEPASS,
                        discord_role=GuildRoles.OWNS_GAMEPASS,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=False,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[],
                    owns_assets=[],
                    verified=True,
                ),
            ),
            MockBindScenario(
                test_cases=[
                    AssetBindTestCase(
                        test_fixture=BindTestFixtures.ASSETS.ASSET_BIND,
                        asset=MockAssets.VIP,
                        asset_type=AssetTypes.CATALOG_ITEM,
                        discord_role=GuildRoles.OWNS_CATALOG_ITEM,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=True,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[],
                    owns_assets=[MockAssets.VIP],
                    verified=True,
                ),
            ),
            MockBindScenario(
                test_cases=[
                    AssetBindTestCase(
                        test_fixture=BindTestFixtures.ASSETS.ASSET_BIND,
                        asset=MockAssets.VIP,
                        asset_type=AssetTypes.CATALOG_ITEM,
                        discord_role=GuildRoles.OWNS_CATALOG_ITEM,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=False,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[],
                    owns_assets=[],
                    verified=True,
                ),
            ),
            MockBindScenario(
                test_cases=[
                    AssetBindTestCase(
                        test_fixture=BindTestFixtures.ASSETS.ASSET_BIND,
                        asset=MockAssets.VIP,
                        asset_type=AssetTypes.BADGE,
                        discord_role=GuildRoles.OWNS_BADGE,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=False,
                        ),
                    ),
                    AssetBindTestCase(
                        test_fixture=BindTestFixtures.ASSETS.ASSET_BIND,
                        asset=MockAssets.VIP,
                        asset_type=AssetTypes.CATALOG_ITEM,
                        discord_role=GuildRoles.OWNS_CATALOG_ITEM,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=False,
                        ),
                    ),
                    AssetBindTestCase(
                        test_fixture=BindTestFixtures.ASSETS.ASSET_BIND,
                        asset=MockAssets.VIP,
                        asset_type=AssetTypes.GAMEPASS,
                        discord_role=GuildRoles.OWNS_GAMEPASS,
                        expected_result=ExpectedBindsResult(
                            expected_bind_success=False,
                        ),
                    ),
                ],
                mock_user=MockUserData(
                    current_discord_roles=[],
                    owns_assets=[],
                    verified=False,
                ),
            ),
        ],
        indirect=True,
    )
    @pytest.mark.asyncio()
    async def test_badge_bind(
        self,
        test_guild: GuildSerializable,
        mock_bind_scenario: MockedBindScenarioResult,
    ):
        """Test the badge bind logic"""

        await _assert_successful_binds_results(
            mocked_bind_scenario=mock_bind_scenario,
            guild_roles=test_guild.roles,
        )


class TestBindHash:
    """Test the bind hash logic"""

    @pytest.mark.asyncio()
    async def test_bind_hash_does_not_equal_different_bind(self):
        """Test the bind hash logic with different bind criteria"""

        bind_1 = GuildBind(
            roles=["1", "2", "3"],
            nickname="test",
            remove_roles=["4", "5", "6"],
            criteria=BindCriteria(
                type="group",
                id=1,
                group=GroupBindData(
                    everyone=True,
                ),
            ),
        )

        bind_2 = GuildBind(
            roles=["1", "2", "3"],
            nickname="test",
            remove_roles=["4", "5", "6"],
            criteria=BindCriteria(
                type="group",
                id=1,
                group=GroupBindData(
                    dynamicRoles=True,
                ),
            ),
        )

        assert hash(bind_1) != hash(bind_2)

    @pytest.mark.asyncio()
    async def test_bind_hash_equals(self):
        """Test the bind hash logic with the same bind criteria and roles"""

        bind_1 = GuildBind(
            roles=["1", "2", "3"],
            nickname="test",
            remove_roles=["4", "5", "6"],
            criteria=BindCriteria(
                type="group",
                id=1,
                group=GroupBindData(
                    everyone=True,
                ),
            ),
        )

        bind_2 = GuildBind(
            roles=["1", "2", "3"],
            nickname="test",
            remove_roles=["4", "5", "6"],
            criteria=BindCriteria(
                type="group",
                id=1,
                group=GroupBindData(
                    everyone=True,
                ),
            ),
        )

        assert hash(bind_1) == hash(bind_2)

    @pytest.mark.asyncio()
    async def test_bind_hash_equals_with_data(self):
        """Test the bind hash logic with a different display name."""

        bind_1 = GuildBind(
            roles=["1", "2", "3"],
            nickname="test",
            remove_roles=["4", "5", "6"],
            criteria=BindCriteria(
                type="group",
                id=1,
                group=GroupBindData(
                    everyone=True,
                ),
            ),
            data=BindData(
                displayName="test 1",
            ),
        )

        bind_2 = GuildBind(
            roles=["1", "2", "3"],
            nickname="test",
            remove_roles=["4", "5", "6"],
            criteria=BindCriteria(
                type="group",
                id=1,
                group=GroupBindData(
                    everyone=True,
                ),
            ),
            data=BindData(
                displayName="test 2",
            ),
        )

        assert hash(bind_1) == hash(
            bind_2
        ), "Binds should be equal since the display name is mutable but not a part of the criteria of the bind"

    @pytest.mark.asyncio()
    async def test_bind_hash_equals_with_data_and_dynamic_roles(self):
        """Test the bind hash logic with a different display name."""

        bind_1 = GuildBind(
            roles=["1", "2", "3"],
            nickname="test",
            remove_roles=["4", "5", "6"],
            criteria=BindCriteria(
                type="group",
                id=1,
                group=GroupBindData(
                    dynamicRoles=True,
                ),
            ),
            data=BindData(
                displayName="test 1",
            ),
        )

        bind_2 = GuildBind(
            roles=["1", "2", "3"],
            nickname="test",
            remove_roles=["4", "5", "6"],
            criteria=BindCriteria(
                type="group",
                id=1,
                group=GroupBindData(
                    dynamicRoles=True,
                ),
            ),
            data=BindData(
                displayName="test 2",
            ),
        )

        assert hash(bind_1) == hash(bind_2)

    @pytest.mark.asyncio()
    async def test_bind_hash_includes_dynamic_roles(self):
        """Test that dynamicRoles field is included in hash calculation to prevent collisions in delete_bind."""

        bind_1 = GuildBind(
            roles=["111111111"],
            nickname="test",
            remove_roles=["222222222"],
            criteria=BindCriteria(
                type="group",
                id=9999999,
                group=GroupBindData(
                    everyone=False,
                    guest=False,
                    min=None,
                    max=None,
                    roleset=None,
                    dynamicRoles=False,
                ),
            ),
        )

        bind_2 = GuildBind(
            roles=["111111111"],
            nickname="test",
            remove_roles=["222222222"],
            criteria=BindCriteria(
                type="group",
                id=9999999,
                group=GroupBindData(
                    everyone=False,
                    guest=False,
                    min=None,
                    max=None,
                    roleset=None,
                    dynamicRoles=True,  # Different from bind_1
                ),
            ),
        )

        assert hash(bind_1.criteria.group) != hash(
            bind_2.criteria.group
        ), "GroupBindData should have different hashes when dynamicRoles differs"
        assert hash(bind_1) != hash(
            bind_2
        ), "GuildBind should have different hashes when dynamicRoles differs"

        group_data_1 = bind_1.criteria.group
        group_data_2 = bind_2.criteria.group

        assert group_data_1.dynamicRoles != group_data_2.dynamicRoles
        assert hash(group_data_1) != hash(group_data_2)


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
