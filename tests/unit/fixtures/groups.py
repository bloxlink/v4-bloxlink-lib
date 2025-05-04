from enum import Enum
import pytest
from bloxlink_lib import RobloxGroup, GroupRoleset, find
from tests.unit.utils import generate_snowflake

__all__ = [
    "GroupRolesets",
    "GroupRolesetsType",
    "guest_roleset",
    "member_roleset",
    "group_rolesets",
    "test_group",
    "find_group_roleset",
]


class GroupRolesets(Enum):
    """The Rolesets for the test group"""

    GUEST = 0
    MEMBER = 1
    OFFICER = 2
    COMMANDER = 3
    ADMIN = 4


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


@pytest.fixture(scope="function")
def guest_roleset() -> GroupRoleset:
    """Initial Guest Roleset for the Group."""

    new_roleset = _create_roleset(GroupRolesets.GUEST)

    return new_roleset


@pytest.fixture(scope="function")
def member_roleset() -> GroupRoleset:
    """Initial Member Roleset for the Group."""

    new_roleset = _create_roleset(GroupRolesets.MEMBER)

    return new_roleset


@pytest.fixture(scope="function")
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


@pytest.fixture(scope="function")
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
