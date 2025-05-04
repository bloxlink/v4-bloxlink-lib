from enum import Enum
import pytest
from bloxlink_lib import RobloxGroup, GroupRoleset, find
from tests.unit.utils import generate_snowflake

__all__ = [
    "GroupRolesets",
    "GroupRolesetsType",
    "member_roleset",
    "group_rolesets",
    "test_group",
]


class GroupRolesets(Enum):
    """The Rolesets for the test group"""

    GUEST = "Guest"
    MEMBER = "Member"
    RANK_1 = "Officer"
    RANK_2 = "Commander"
    ADMIN = "Leader"


GroupRolesetsType = dict[int, GroupRoleset]


def _create_roleset(
    roleset_name: str, existing_rolesets: GroupRolesetsType
) -> GroupRoleset:
    new_snowflake = generate_snowflake()

    new_roleset = GroupRoleset(
        name=roleset_name,
        rank=len(existing_rolesets) + 1,
        member_count=100,
        id=new_snowflake,
    )

    return new_roleset


@pytest.fixture(scope="module")
def member_roleset() -> GroupRoleset:
    """Initial Member Roleset for the Group."""

    existing_rolesets: GroupRolesetsType = {}

    new_roleset = _create_roleset(GroupRolesets.MEMBER, existing_rolesets)

    return new_roleset


@pytest.fixture(scope="module")
def group_rolesets(member_roleset: GroupRoleset) -> GroupRolesetsType:
    """Military test group rolesets"""

    rolesets: GroupRolesetsType = {member_roleset.rank: member_roleset}

    for roleset in GroupRolesets:
        # make sure we don't double-create roles
        if find(lambda r: r.name == roleset.value, rolesets.values()):
            continue

        new_roleset = _create_roleset(roleset.value, rolesets)
        rolesets[new_roleset.rank] = new_roleset

    return rolesets


@pytest.fixture(scope="module")
def test_group(group_rolesets: GroupRolesetsType) -> RobloxGroup:
    """Military test group"""

    return RobloxGroup(
        id=generate_snowflake(),
        name="Military Roleplay Community",
        rolesets=group_rolesets,
    )
