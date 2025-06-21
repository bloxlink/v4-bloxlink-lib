from enum import Enum
from typing import Callable
from pydantic.dataclasses import dataclass
import pytest

from bloxlink_lib import BloxlinkEntity, GuildBind, RoleSerializable
from bloxlink_lib.models import binds
from bloxlink_lib.test_utils.fixtures import (
    assets as asset_fixtures,
    groups as group_fixtures,
)
from bloxlink_lib.test_utils.fixtures.guilds import GuildRoles
from bloxlink_lib.test_utils.mockers import mock_bind


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


class VerifiedTestFixtures(Enum):
    """The fixtures for verified bind tests"""

    VERIFIED_BIND = "verified_bind"
    UNVERIFIED_BIND = "unverified_bind"


@dataclass
class BindTestFixtures:
    """The fixtures for all bind tests"""

    ASSETS = asset_fixtures.AssetTestFixtures
    GROUPS = group_fixtures.GroupTestFixtures
    VERIFIED = VerifiedTestFixtures
