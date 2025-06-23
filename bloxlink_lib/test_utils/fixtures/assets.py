from enum import Enum, auto
import pytest
from typing import Callable

from bloxlink_lib.models import binds
from bloxlink_lib import create_entity, RoleSerializable
from bloxlink_lib.test_utils.fixtures.guilds import GuildRoles, find_discord_roles
from bloxlink_lib.test_utils import mock_bind


class AssetTypes(Enum):
    """The types of assets available for mocking"""

    BADGE = "badge"
    GAMEPASS = "gamepass"
    CATALOG_ITEM = "asset"


class MockAssets(Enum):
    """The assets available for mocking"""

    VIP = 1
    DONATOR = auto()


class AssetTestFixtures(Enum):
    """The test fixtures for asset binds"""

    ASSET_BIND = "asset_bind"


# Asset bind fixtures
@pytest.fixture()
def asset_bind(
    mocker,
    find_discord_roles: Callable[[GuildRoles], list[RoleSerializable]],
) -> Callable[[AssetTypes, int, GuildRoles], binds.GuildBind]:
    """Bind an asset to receive these specific roles"""

    def _get_bind_for_asset(
        asset_type: AssetTypes,
        asset_id: int,
        discord_role: GuildRoles,
    ) -> binds.GuildBind:
        return mock_bind(
            mocker,
            discord_roles=find_discord_roles(discord_role),
            criteria=binds.BindCriteria(type=asset_type.value, id=asset_id),
            entity=create_entity(asset_type.value, asset_id),
        )

    return _get_bind_for_asset


__all__ = [
    "MockAssets",
    "AssetTypes",
    "asset_bind",
] + [fixture.value for fixture in AssetTestFixtures]
