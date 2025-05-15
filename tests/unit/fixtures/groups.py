from enum import Enum, auto
from typing import Callable
import pytest
from bloxlink_lib import (
    RobloxGroup,
    GroupBindData,
    find,
    RoleSerializable,
    GroupRoleset,
)
from bloxlink_lib.models import binds
from tests.unit.utils import generate_snowflake, mock_bind
from tests.unit.fixtures.guilds import GuildRoles


class GroupTestFixtures(Enum):
    """The test fixtures for group binds"""

    GROUP_BIND = "group_bind"
    DYNAMIC_ROLES_GROUP_BIND = "dynamic_roles_group_bind"
    GUEST_GROUP_BIND = "guest_group_bind"
    ROLESET_GROUP_BIND = "roleset_group_bind"
    MIN_MAX_GROUP_BIND = "min_max_group_bind"
    EVERYONE_GROUP_BIND = "everyone_group_bind"


class GroupRolesets(Enum):
    """The Rolesets for the test group"""

    GUEST = 0
    MEMBER = auto()
    OFFICER = auto()
    COMMANDER = auto()
    ADMIN = auto()


GroupRolesetsType = dict[int, GroupRoleset]


def _create_roleset(roleset: GroupRolesets) -> GroupRoleset:
    new_snowflake = generate_snowflake()

    new_roleset = GroupRoleset(
        name=roleset.name.title(),
        rank=roleset.value,
        member_count=100,
        id=new_snowflake,
    )

    return new_roleset


@pytest.fixture()
def guest_roleset() -> GroupRoleset:
    """Initial Guest Roleset for the Group."""

    new_roleset = _create_roleset(GroupRolesets.GUEST)

    return new_roleset


@pytest.fixture()
def member_roleset() -> GroupRoleset:
    """Initial Member Roleset for the Group."""

    new_roleset = _create_roleset(GroupRolesets.MEMBER)

    return new_roleset


@pytest.fixture()
def group_rolesets(
    guest_roleset: GroupRoleset, member_roleset: GroupRoleset
) -> GroupRolesetsType:
    """Military test group rolesets"""

    rolesets: GroupRolesetsType = {
        guest_roleset.rank: guest_roleset,
        member_roleset.rank: member_roleset,
    }

    for roleset in GroupRolesets:
        # make sure we don't double-create roles
        if find(lambda r: r.name == roleset.name.title(), rolesets.values()):
            continue

        new_roleset = _create_roleset(roleset)
        rolesets[new_roleset.rank] = new_roleset

    return rolesets


@pytest.fixture()
def test_group(group_rolesets: GroupRolesetsType) -> RobloxGroup:
    """Military test group"""

    return RobloxGroup(
        id=generate_snowflake(),
        name="Military Roleplay Community",
        rolesets=group_rolesets,
    )


@pytest.fixture()
def find_group_roleset(group_rolesets: GroupRolesetsType) -> GroupRoleset:
    """Retrieve the Discord roles from the GuildRoles enum"""

    def _find_roleset(role_enum: GroupRolesets) -> GroupRoleset:
        return find(lambda r: r.name == role_enum.value, group_rolesets.values())

    return _find_roleset


# Group bind fixtures
@pytest.fixture()
def everyone_group_bind(
    mocker,
    find_discord_roles: Callable[[GuildRoles], list[RoleSerializable]],
    test_group: RobloxGroup,
) -> binds.GuildBind:
    """Bind everyone to receive these specific roles"""

    mocked_bind = mock_bind(
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

    mocked_bind = mock_bind(
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

    mocked_bind = mock_bind(
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

    mocked_bind = mock_bind(
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

    mocked_bind = mock_bind(
        mocker,
        discord_roles=find_discord_roles(GuildRoles.COMMANDER, GuildRoles.ADMIN),
        criteria=binds.BindCriteria(
            type="group",
            id=test_group.id,
            group=binds.GroupBindData(
                min=GroupRolesets.COMMANDER, max=GroupRolesets.ADMIN
            ),
        ),
        entity=test_group,
    )

    return mocked_bind


@pytest.fixture()
def group_bind(
    mocker,
    find_discord_roles: Callable[[GuildRoles], list[RoleSerializable]],
) -> Callable[[RobloxGroup, binds.GroupBindData, GuildRoles], binds.GuildBind]:
    """Bind a group to receive these specific roles"""

    def _get_bind_for_group(
        group: RobloxGroup,
        group_criteria: binds.GroupBindData,
        discord_role: GuildRoles,
    ) -> binds.GuildBind:
        return mock_bind(
            mocker,
            discord_roles=find_discord_roles(discord_role),
            criteria=binds.BindCriteria(
                type="group", id=group.value, group=group_criteria
            ),
            entity=RobloxGroup(id=group.value),
        )

    return _get_bind_for_group


__all__ = [
    "GroupRolesets",
    "GroupRolesetsType",
    "guest_roleset",
    "member_roleset",
    "group_rolesets",
    "test_group",
    "find_group_roleset",
] + [fixture.value for fixture in GroupTestFixtures]
