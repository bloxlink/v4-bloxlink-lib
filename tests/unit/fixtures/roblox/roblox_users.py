from datetime import datetime
import pytest
from bloxlink_lib import RobloxUser, RobloxUserGroup, GroupRoleset, RobloxGroup, find
from tests.unit.utils import generate_snowflake

# fixtures
from tests.unit.fixtures.roblox.groups import test_military_group, MEMBER_ROLESET_NAME


def _mock_roblox_user(
    mocker, *, username: str, groups: dict[int, RobloxUserGroup]
) -> RobloxUser:
    roblox_user = RobloxUser(
        id=generate_snowflake(),
        username=username,
        display_name=username.title(),
        created=datetime.fromisoformat("2021-01-01T00:00:00.000000+00:00").replace(
            tzinfo=None
        ),
        groups=groups,
    )

    # Do not sync the model with the Roblox API
    mocked_sync = mocker.AsyncMock(return_value=None)
    mocker.patch.object(RobloxUser, "sync", new=mocked_sync)

    return roblox_user


@pytest.fixture()
def test_military_group_member(mocker, test_military_group: RobloxGroup) -> RobloxUser:
    """Test RobloxUser model in the military group."""

    member_roleset = find(
        lambda r: r.name == MEMBER_ROLESET_NAME, test_military_group.rolesets.values()
    )

    if not member_roleset:
        raise ValueError("member_roleset should be in the Roblox user mock model")

    roblox_user = _mock_roblox_user(
        mocker,
        username="john",
        groups={
            test_military_group.id: RobloxUserGroup(
                group=test_military_group, role=member_roleset
            )
        },
    )

    return roblox_user


@pytest.fixture()
def test_roblox_user_military_group_guest(mocker) -> RobloxUser:
    """Test RobloxUser model."""

    roblox_user = _mock_roblox_user(mocker, username="bob", groups={})

    return roblox_user
