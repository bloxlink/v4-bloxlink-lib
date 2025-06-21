from typing import TYPE_CHECKING, Callable, Annotated
import pytest
from pydantic import Field
from bloxlink_lib import (
    RobloxGroup,
    find,
    BaseModel,
    RobloxUserGroup,
    GuildBind,
    GuildSerializable,
)
from bloxlink_lib.test_utils.fixtures import (
    GuildRoles,
    MockAssets,
    AssetTypes,
)
from bloxlink_lib.test_utils.mockers import MockUserData, MockUser, mock_user
from bloxlink_lib.test_utils.fixtures.binds import BindTestFixtures
from tests.unit.utils import enum_list_to_value_list

if TYPE_CHECKING:
    from . import GuildRolesType, GroupRolesetsType


class ExpectedBindsResult(BaseModel):
    """Data to use for the mocked user in a test case"""

    expected_remove_roles: Annotated[
        list[GuildRoles | int], Field(default_factory=list)
    ]  # Passed to MockUser to use in the test case. Defaults to empty array.
    expected_bind_success: bool  # Whether the user meets the bind criteria. Passed to MockUser to use in the test case.


class BindTestCase(BaseModel):
    """The base class for all bind test cases"""

    test_fixture: (
        BindTestFixtures.ASSETS | BindTestFixtures.GROUPS | BindTestFixtures.VERIFIED
    )  # The fixture to use for the bind test case
    expected_result: ExpectedBindsResult  # The expected result of the bind test case


class AssetBindTestCase(BindTestCase):
    """The test case for asset binds"""

    asset: MockAssets
    asset_type: AssetTypes
    discord_role: GuildRoles


class MockBindScenario(BaseModel):
    """Data to use for the mocked user in a test case"""

    mock_user: MockUserData
    test_cases: Annotated[list[BindTestCase | AssetBindTestCase], Field(min_length=1)]


class MockedBindScenarioResult(BaseModel):
    """Data to use for the mocked user in a test case"""

    test_against_binds: list[GuildBind]
    mock_user: MockUser
    expected_results: list[ExpectedBindsResult]


# Bind test case fixtures
@pytest.fixture()
def mock_bind_scenario(
    request,
    mocker,
    test_guild: GuildSerializable,
    test_group: RobloxGroup,
    group_rolesets: "GroupRolesetsType",
    guild_roles: "GuildRolesType",
) -> MockedBindScenarioResult:
    """Data to use for the mocked user in a test case"""

    mock_bind_scenario: MockBindScenario = request.param

    current_discord_roles: list[int] = [
        r.id
        for r in guild_roles.values()
        if r.name
        in enum_list_to_value_list(mock_bind_scenario.mock_user.current_discord_roles)
    ]

    mock_user_data: MockUserData = mock_bind_scenario.mock_user
    test_cases = mock_bind_scenario.test_cases
    test_against_binds: list[GuildBind] = []

    if mock_user_data.current_group_roleset:
        current_group_roleset = (
            find(
                lambda r: r.name == mock_user_data.current_group_roleset.name.title(),
                group_rolesets.values(),
            )
            if mock_user_data.current_group_roleset
            else None
        )

        if not current_group_roleset:
            raise ValueError("Unable to find matching Roleset from Mocked Group")
    else:
        current_group_roleset = None

    for test_case in test_cases:
        if test_case.expected_result.expected_remove_roles:
            test_case.expected_result.expected_remove_roles = [
                r.id
                for r in guild_roles.values()
                if r.name
                in enum_list_to_value_list(
                    test_case.expected_result.expected_remove_roles
                )
            ]

        match test_case.test_fixture:
            case BindTestFixtures.ASSETS.ASSET_BIND:
                asset_bind_callable: Callable[
                    [AssetTypes, int, GuildRoles], GuildBind
                ] = request.getfixturevalue(test_case.test_fixture.value)
                bind_fixture = asset_bind_callable(
                    test_case.asset_type,
                    test_case.asset.value,
                    test_case.discord_role,
                )
                test_against_binds.append(bind_fixture)
            case _:
                bind_fixture = request.getfixturevalue(test_case.test_fixture.value)
                test_against_binds.append(bind_fixture)

    user = mock_user(
        mocker,
        verified=mock_user_data.verified,
        username="john",
        guild=test_guild,
        groups=(
            {
                test_group.id: RobloxUserGroup(
                    group=test_group, role=current_group_roleset
                )
            }
            if current_group_roleset
            else None
        ),
        owns_assets=mock_user_data.owns_assets or [],
        current_discord_roles=current_discord_roles,
    )

    scenario_result = MockedBindScenarioResult(
        mock_user=user,
        test_against_binds=test_against_binds,
        expected_results=[test_case.expected_result for test_case in test_cases],
    )

    return scenario_result


__all__ = [
    "ExpectedBindsResult",
    "MockBindScenario",
    "MockedBindScenarioResult",
    "AssetBindTestCase",
    "BindTestCase",
    "BindTestFixtures",
    "mock_bind_scenario",
]
