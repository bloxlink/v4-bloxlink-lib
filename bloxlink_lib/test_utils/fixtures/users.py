import pytest
from bloxlink_lib import (
    GuildSerializable,
    RobloxUserGroup,
    RobloxGroup,
    GroupRoleset,
)
from bloxlink_lib.test_utils.mockers import MockUser, mock_user

__all__ = [
    "test_group_member",
    "test_group_member_bracketed_roleset",
]


@pytest.fixture()
def test_group_member(
    mocker,
    test_guild: GuildSerializable,
    test_group: RobloxGroup,
    member_roleset: GroupRoleset,
) -> MockUser:
    """Test Discord Member model."""

    user = mock_user(
        mocker,
        verified=True,
        username="john",
        guild=test_guild,
        groups={test_group.id: RobloxUserGroup(group=test_group, role=member_roleset)},
    )

    return user


@pytest.fixture()
def test_group_member_bracketed_roleset(
    mocker,
    test_guild: GuildSerializable,
    test_group: RobloxGroup,
) -> MockUser:
    """Test Discord Member model with a bracketed roleset"""

    user = mock_user(
        mocker,
        verified=True,
        username="john",
        guild=test_guild,
        groups={
            test_group.id: RobloxUserGroup(
                group=test_group,
                role=GroupRoleset(
                    name="[L1] Recruit",
                    rank=1,
                    id=1,
                    memberCount=1,
                ),
            )
        },
    )

    return user
