from enum import Enum
from typing import TYPE_CHECKING, Callable, Annotated
import pytest
from pydantic import Field
from pydantic.dataclasses import dataclass
from bloxlink_lib.models import binds
from bloxlink_lib import (
    RobloxGroup,
    find,
    BloxlinkEntity,
    BaseModel,
    RobloxUserGroup,
    GuildBind,
    GuildSerializable,
    RoleSerializable,
)
from tests.unit.fixtures.badges import MockBadges, BadgeTestFixtures
from tests.unit.fixtures.groups import GroupTestFixtures
from tests.unit.utils import enum_list_to_value_list, mock_bind
from . import GuildRoles, MockUserData, MockUser, mock_user

if TYPE_CHECKING:
    from . import GuildRolesType, GroupRolesetsType


class VerifiedTestFixtures(Enum):
    """The fixtures for verified bind tests"""

    VERIFIED_BIND = "verified_bind"
    UNVERIFIED_BIND = "unverified_bind"


@dataclass
class BindTestFixtures:
    """The fixtures for all bind tests"""

    BADGES = BadgeTestFixtures
    GROUPS = GroupTestFixtures
    VERIFIED = VerifiedTestFixtures


class ExpectedBindsResult(BaseModel):
    """Data to use for the mocked user in a test case"""

    expected_remove_roles: Annotated[
        list[GuildRoles | int], Field(default_factory=list)
    ]  # Passed to MockUser to use in the test case. Defaults to empty array.
    expected_bind_success: bool  # Whether the user meets the bind criteria. Passed to MockUser to use in the test case.


class BindTestCase(BaseModel):
    """The base class for all bind test cases"""

    test_fixture: (
        BindTestFixtures.BADGES | BindTestFixtures.GROUPS | BindTestFixtures.VERIFIED
    )  # The fixture to use for the bind test case
    expected_result: ExpectedBindsResult  # The expected result of the bind test case


class BadgeBindTestCase(BindTestCase):
    """The test case for badge binds"""

    badge: MockBadges
    discord_role: GuildRoles


class MockBindScenario(BaseModel):
    """Data to use for the mocked user in a test case"""

    mock_user: MockUserData
    test_cases: Annotated[list[BindTestCase | BadgeBindTestCase], Field(min_length=1)]


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
            case BindTestFixtures.BADGES.BADGE_BIND:
                badge_bind_callable: Callable[[MockBadges, GuildRoles], GuildBind] = (
                    request.getfixturevalue(test_case.test_fixture.value)
                )
                bind_fixture = badge_bind_callable(
                    test_case.badge, test_case.discord_role
                )
                test_against_binds.append(bind_fixture)
            case _:
                print("test_case.test_fixture", test_case.test_fixture)
                bind_fixture = request.getfixturevalue(test_case.test_fixture.value)
                print("bind_fixture", bind_fixture)
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


# Bind utility fixtures
@pytest.fixture()
def find_discord_roles(guild_roles: "GuildRolesType") -> list[RoleSerializable]:
    """Retrieve the Discord roles from the GuildRoles enum"""

    def _find_discord_roles(*role_enums: GuildRoles) -> list[RoleSerializable]:
        return [
            find(lambda r: r.name == role_enum.value, guild_roles.values())
            for role_enum in role_enums
        ]

    return _find_discord_roles


# Verified bind fixtures
@pytest.fixture()
def verified_bind(
    mocker,
    find_discord_roles: Callable[[GuildRoles], list[RoleSerializable]],
) -> binds.GuildBind:
    """Bind everyone to receive these specific roles"""

    mocked_bind = mock_bind(
        mocker,
        discord_roles=find_discord_roles(GuildRoles.VERIFIED),
        criteria=binds.BindCriteria(type="verified"),
        entity=BloxlinkEntity(type="verified"),
    )

    return mocked_bind


# Unverified bind fixtures
@pytest.fixture()
def unverified_bind(
    mocker,
    find_discord_roles: Callable[[GuildRoles], list[RoleSerializable]],
) -> binds.GuildBind:
    """Bind everyone to receive these specific roles"""

    mocked_bind = mock_bind(
        mocker,
        discord_roles=find_discord_roles(GuildRoles.UNVERIFIED),
        criteria=binds.BindCriteria(type="unverified"),
        entity=BloxlinkEntity(type="unverified"),
    )

    return mocked_bind


__all__ = [
    "ExpectedBindsResult",
    "MockBindScenario",
    "MockedBindScenarioResult",
    "find_discord_roles",
    "BadgeBindTestCase",
    "BindTestCase",
    "BindTestFixtures",
    "mock_bind_scenario",
] + [fixture.value for fixture in VerifiedTestFixtures]
