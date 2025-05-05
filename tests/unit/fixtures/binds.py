from enum import Enum
from typing import TYPE_CHECKING, Callable, Annotated
import pytest
from pydantic import Field
from bloxlink_lib.models import binds
from bloxlink_lib import (
    RobloxGroup,
    GroupBindData,
    find,
    BloxlinkEntity,
    BaseModel,
    RobloxUserGroup,
    GuildBind,
    RobloxEntity,
    GuildSerializable,
    RoleSerializable,
    RobloxBadge,
)
from tests.unit.fixtures.badges import MockBadges
from . import GuildRoles, MockUserData, MockUser, mock_user, GroupRolesets
from tests.unit.utils import enum_list_to_value_list

if TYPE_CHECKING:
    from . import GuildRolesType, GroupRolesetsType

__all__ = [
    "ExpectedBinds",
    "MockBindScenario",
    "MockedBindScenarioResult",
    "find_discord_roles",
    "everyone_group_bind",
    "mock_bind_scenario",
    "dynamic_roles_group_bind",
    "roleset_group_bind",
    "min_max_group_bind",
    "guest_group_bind",
    "verified_bind",
    "unverified_bind",
    "badge_bind",
    "BadgeBindTestCase",
    "BindTestFixtures",
]


class BindTestFixtures(Enum):
    """The fixtures for all bind tests"""

    EVERYONE_GROUP_BIND = "everyone_group_bind"
    DYNAMIC_ROLES_GROUP_BIND = "dynamic_roles_group_bind"
    ROLES_GROUP_BIND = "roles_group_bind"
    MIN_MAX_GROUP_BIND = "min_max_group_bind"
    GUEST_GROUP_BIND = "guest_group_bind"
    VERIFIED_BIND = "verified_bind"
    UNVERIFIED_BIND = "unverified_bind"
    BADGE_BIND = "badge_bind"


class ExpectedBinds(BaseModel):
    """Data to use for the mocked user in a test case"""

    expected_remove_roles: Annotated[
        list[GuildRoles | int], Field(default_factory=list)
    ]  # Passed to MockUser to use in the test case. Defaults to empty array.
    expected_bind_success: bool  # Whether the user meets the bind criteria. Passed to MockUser to use in the test case.


class BindTestCase(BaseModel):
    """The base class for all bind test cases"""

    test_fixture: str  # The fixture to use for the bind test case


class BadgeBindTestCase(BindTestCase):
    """The test case for badge binds"""

    badge: MockBadges
    discord_role: GuildRoles


class ExtraBindResultData(BaseModel):
    """Extra data to use for the mocked user"""

    owns_assets: list[MockBadges] | None = None


class MockBindScenario(BaseModel):
    """Data to use for the mocked user in a test case"""

    test_against_bind_fixtures: list[str] = (
        None  # Passed to MockedBindScenarioResult to use in the test case
    )
    mock_user: MockUserData
    expected_binds: ExpectedBinds = None
    test_cases: list[BadgeBindTestCase] = None


class MockedBindScenarioResult(BaseModel):
    """Data to use for the mocked user in a test case"""

    test_against_bind_fixtures: list[
        GuildBind | Callable[..., GuildBind]
    ]  # it's either a GuildBind or a function that returns a GuildBind if custom arguments are necessary
    mock_user: MockUser
    expected_binds: ExpectedBinds


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
    expected_binds: ExpectedBinds = mock_bind_scenario.expected_binds
    test_against_bind_fixtures: list[GuildBind | Callable[..., GuildBind]] = [
        request.getfixturevalue(fixture)
        for fixture in mock_bind_scenario.test_against_bind_fixtures or []
    ]
    test_cases = mock_bind_scenario.test_cases

    if expected_binds.expected_remove_roles:
        expected_binds.expected_remove_roles = [
            r.id
            for r in guild_roles.values()
            if r.name in enum_list_to_value_list(expected_binds.expected_remove_roles)
        ]

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

    if test_cases:
        for test_case in test_cases:
            match test_case.test_fixture:
                case BindTestFixtures.BADGE_BIND:
                    badge_bind_callable: Callable[
                        [MockBadges, GuildRoles], GuildBind
                    ] = request.getfixturevalue(test_case.test_fixture)
                    bind_fixture = badge_bind_callable(
                        test_case.badge, test_case.discord_role
                    )
                    test_against_bind_fixtures.append(bind_fixture)

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
        test_against_bind_fixtures=test_against_bind_fixtures,
        expected_binds=expected_binds,
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


def _mock_bind(
    mocker,
    *,
    discord_roles: list[RoleSerializable],
    criteria: binds.BindCriteria,
    entity: RobloxEntity,
    nickname: str = "{roblox-name}",
) -> binds.GuildBind:
    """Mock a bind"""

    new_bind = binds.GuildBind(
        nickname=nickname,
        roles=[str(role.id) for role in discord_roles],
        criteria=criteria,
    )

    # Mock the sync method to prevent actual API calls
    mocked_sync = mocker.AsyncMock(return_value=None)
    mocker.patch.object(RobloxGroup, "sync", new=mocked_sync)

    new_bind.entity = entity

    return new_bind


# Group bind fixtures
@pytest.fixture()
def everyone_group_bind(
    mocker,
    find_discord_roles: Callable[[GuildRoles], list[RoleSerializable]],
    test_group: RobloxGroup,
) -> binds.GuildBind:
    """Bind everyone to receive these specific roles"""

    mocked_bind = _mock_bind(
        mocker,
        discord_roles=find_discord_roles(GuildRoles.OFFICER),
        criteria=binds.BindCriteria(
            type="group", id=test_group.id, group=GroupBindData(everyone=True)
        ),
        entity=test_group,
    )

    return mocked_bind


@pytest.fixture()
def dynamic_roles_group_bind(
    mocker,
    test_group: RobloxGroup,
) -> binds.GuildBind:
    """Bind every group roleset to the same name Discord role"""

    mocked_bind = _mock_bind(
        mocker,
        discord_roles=[],
        criteria=binds.BindCriteria(
            type="group", id=test_group.id, group=GroupBindData(dynamicRoles=True)
        ),
        entity=test_group,
    )

    return mocked_bind


@pytest.fixture()
def guest_group_bind(
    mocker,
    test_group: RobloxGroup,
    find_discord_roles: Callable[[GuildRoles], list[RoleSerializable]],
) -> binds.GuildBind:
    """Bind a non-group member to receive these specific roles"""

    mocked_bind = _mock_bind(
        mocker,
        discord_roles=find_discord_roles(GuildRoles.NOT_IN_GROUP),
        criteria=binds.BindCriteria(
            type="group", id=test_group.id, group=GroupBindData(guest=True)
        ),
        entity=test_group,
    )

    return mocked_bind


@pytest.fixture()
def roleset_group_bind(
    mocker,
    test_group: RobloxGroup,
    find_discord_roles: Callable[[GuildRoles], list[RoleSerializable]],
) -> binds.GuildBind:
    """Bind a specific roleset to receive these specific roles"""

    mocked_bind = _mock_bind(
        mocker,
        discord_roles=find_discord_roles(GuildRoles.COMMANDER),
        criteria=binds.BindCriteria(
            type="group",
            id=test_group.id,
            group=GroupBindData(roleset=GroupRolesets.COMMANDER.value),
        ),
        entity=test_group,
    )

    return mocked_bind


@pytest.fixture()
def min_max_group_bind(
    mocker,
    test_group: RobloxGroup,
    find_discord_roles: Callable[[GuildRoles], list[RoleSerializable]],
) -> binds.GuildBind:
    """Bind a range of rolesets to receive these specific roles"""

    mocked_bind = _mock_bind(
        mocker,
        discord_roles=find_discord_roles(GuildRoles.COMMANDER, GuildRoles.ADMIN),
        criteria=binds.BindCriteria(
            type="group",
            id=test_group.id,
            group=GroupBindData(min=GroupRolesets.COMMANDER, max=GroupRolesets.ADMIN),
        ),
        entity=test_group,
    )

    return mocked_bind


# Verified bind fixtures
@pytest.fixture()
def verified_bind(
    mocker,
    find_discord_roles: Callable[[GuildRoles], list[RoleSerializable]],
) -> binds.GuildBind:
    """Bind everyone to receive these specific roles"""

    mocked_bind = _mock_bind(
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

    mocked_bind = _mock_bind(
        mocker,
        discord_roles=find_discord_roles(GuildRoles.UNVERIFIED),
        criteria=binds.BindCriteria(type="unverified"),
        entity=BloxlinkEntity(type="unverified"),
    )

    return mocked_bind


# Badge bind fixtures
@pytest.fixture()
def badge_bind(
    mocker,
    find_discord_roles: Callable[[GuildRoles], list[RoleSerializable]],
) -> Callable[[MockBadges, GuildRoles], binds.GuildBind]:
    """Bind a badge to receive these specific roles"""

    def _get_bind_for_badge(
        badge: MockBadges,
        discord_role: GuildRoles,
    ) -> binds.GuildBind:
        return _mock_bind(
            mocker,
            discord_roles=find_discord_roles(discord_role),
            criteria=binds.BindCriteria(type="badge", id=badge.value),
            entity=RobloxBadge(id=badge.value),
        )

    return _get_bind_for_badge
