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
)
from . import (
    GuildRoles,
    MockUserData,
    MockUser,
    mock_user,
)
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
    "guest_group_bind",
    "verified_bind",
    "unverified_bind",
]


class ExpectedBinds(BaseModel):
    """Data to use for the mocked user in a test case"""

    expected_remove_roles: Annotated[
        list[GuildRoles | int], Field(default_factory=list)
    ]  # Passed to MockUser to use in the test case. Defaults to empty array.
    expected_bind_success: bool  # Whether the user meets the bind criteria. Passed to MockUser to use in the test case.


class MockBindScenario(BaseModel):
    """Data to use for the mocked user in a test case"""

    test_against_bind_fixtures: list[
        str
    ]  # Passed to MockedBindScenarioResult to use in the test case
    mock_user: MockUserData
    expected_binds: ExpectedBinds = None


class MockedBindScenarioResult(BaseModel):
    """Data to use for the mocked user in a test case"""

    test_against_bind_fixtures: list[GuildBind]
    mock_user: MockUser
    expected_binds: ExpectedBinds


# Bind test case fixtures
@pytest.fixture(scope="module")
def mock_bind_scenario(
    request,
    module_mocker,
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
    test_against_bind_fixtures: list[GuildBind] = [
        request.getfixturevalue(fixture)
        for fixture in mock_bind_scenario.test_against_bind_fixtures
    ]

    if expected_binds.expected_remove_roles:
        expected_binds.expected_remove_roles = [
            r.id
            for r in guild_roles.values()
            if r.name in enum_list_to_value_list(expected_binds.expected_remove_roles)
        ]

    if mock_user_data.current_group_roleset:
        current_group_roleset = (
            find(
                lambda r: r.name in mock_user_data.current_group_roleset.value,
                group_rolesets.values(),
            )
            if mock_user_data.current_group_roleset
            else None
        )

        if not current_group_roleset:
            raise ValueError("Unable to find matching Roleset from Mocked Group")
    else:
        current_group_roleset = None

    user = mock_user(
        module_mocker,
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
        current_discord_roles=current_discord_roles,
    )

    scenario_result = MockedBindScenarioResult(
        mock_user=user,
        test_against_bind_fixtures=test_against_bind_fixtures,
        expected_binds=expected_binds,
    )

    return scenario_result


# Bind utility fixtures
@pytest.fixture(scope="module")
def find_discord_roles(guild_roles: "GuildRolesType") -> list[RoleSerializable]:
    """Retrieve the Discord roles from the GuildRoles enum"""

    def _find_discord_roles(*role_enums: GuildRoles) -> list[RoleSerializable]:
        return [
            find(lambda r: r.name == role_enum.value, guild_roles.values())
            for role_enum in role_enums
        ]

    return _find_discord_roles


def _mock_bind(
    module_mocker,
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
    mocked_sync = module_mocker.AsyncMock(return_value=None)
    module_mocker.patch.object(RobloxGroup, "sync", new=mocked_sync)

    new_bind.entity = entity

    return new_bind


# Group bind fixtures
@pytest.fixture(scope="module")
def everyone_group_bind(
    module_mocker,
    find_discord_roles: Callable[[GuildRoles, ...], list[RoleSerializable]],
    test_group: RobloxGroup,
) -> binds.GuildBind:
    """Bind everyone to receive these specific roles"""

    mocked_bind = _mock_bind(
        module_mocker,
        discord_roles=find_discord_roles(GuildRoles.RANK_1),
        criteria=binds.BindCriteria(
            type="group", id=test_group.id, group=GroupBindData(everyone=True)
        ),
        entity=test_group,
    )

    return mocked_bind


@pytest.fixture(scope="module")
def dynamic_roles_group_bind(
    module_mocker,
    test_group: RobloxGroup,
) -> binds.GuildBind:
    """Bind every group roleset to the same name Discord role"""

    mocked_bind = _mock_bind(
        module_mocker,
        discord_roles=[],
        criteria=binds.BindCriteria(
            type="group", id=test_group.id, group=GroupBindData(dynamicRoles=True)
        ),
        entity=test_group,
    )

    return mocked_bind


@pytest.fixture(scope="module")
def guest_group_bind(
    module_mocker,
    test_group: RobloxGroup,
    find_discord_roles: Callable[[GuildRoles], list[RoleSerializable]],
) -> binds.GuildBind:
    """Bind a non-group member to receive these specific roles"""

    mocked_bind = _mock_bind(
        module_mocker,
        discord_roles=find_discord_roles(GuildRoles.NOT_IN_GROUP),
        criteria=binds.BindCriteria(
            type="group", id=test_group.id, group=GroupBindData(guest=True)
        ),
        entity=test_group,
    )

    return mocked_bind


# Verified bind fixtures
@pytest.fixture(scope="module")
def verified_bind(
    module_mocker,
    find_discord_roles: Callable[[GuildRoles], list[RoleSerializable]],
) -> binds.GuildBind:
    """Bind everyone to receive these specific roles"""

    mocked_bind = _mock_bind(
        module_mocker,
        discord_roles=find_discord_roles(GuildRoles.VERIFIED),
        criteria=binds.BindCriteria(type="verified"),
        entity=BloxlinkEntity(type="verified"),
    )

    return mocked_bind


# Unverified bind fixtures
@pytest.fixture(scope="module")
def unverified_bind(
    module_mocker,
    find_discord_roles: Callable[[GuildRoles, ...], list[RoleSerializable]],
) -> binds.GuildBind:
    """Bind everyone to receive these specific roles"""

    mocked_bind = _mock_bind(
        module_mocker,
        discord_roles=find_discord_roles(GuildRoles.UNVERIFIED),
        criteria=binds.BindCriteria(type="unverified"),
        entity=BloxlinkEntity(type="unverified"),
    )

    return mocked_bind
