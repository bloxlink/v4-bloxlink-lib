from typing import Final
import pytest
from bloxlink_lib import RobloxGroup, GroupRoleset, find
from tests.unit.utils import generate_snowflake

INITIAL_ROLESET_NAMES: Final[tuple[str, ...]] = [
    "Guest",
    "Member",
    "Officer",
    "Commander",
    "Leader",
]
GUEST_ROLESET_NAME: Final[str] = INITIAL_ROLESET_NAMES[0]
MEMBER_ROLESET_NAME: Final[str] = INITIAL_ROLESET_NAMES[1]

GroupRolesets = dict[int, GroupRoleset]


def _create_roleset(
    roleset_name: str, existing_rolesets: GroupRolesets
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

    existing_rolesets: GroupRolesets = {}

    new_roleset = _create_roleset(MEMBER_ROLESET_NAME, existing_rolesets)

    return new_roleset


@pytest.fixture(scope="module")
def group_rolesets(member_roleset: GroupRoleset) -> GroupRolesets:
    """Military test group rolesets"""

    rolesets: GroupRolesets = {member_roleset.rank: member_roleset}

    for roleset_name in INITIAL_ROLESET_NAMES:
        # make sure we don't double-create roles
        if find(lambda r: r.name == roleset_name, rolesets.values()):
            continue

        new_roleset = _create_roleset(roleset_name, rolesets)
        rolesets[new_roleset.rank] = new_roleset

    return rolesets


@pytest.fixture(scope="module")
def test_test_group(group_rolesets: GroupRolesets) -> RobloxGroup:
    """Military test group"""

    return RobloxGroup(
        id=generate_snowflake(),
        name="Military Roleplay Community",
        rolesets=group_rolesets,
    )
