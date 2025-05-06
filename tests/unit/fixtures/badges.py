from enum import Enum, auto
import pytest
from typing import Callable

from bloxlink_lib.models import binds
from bloxlink_lib import RobloxBadge, RoleSerializable, GuildBind
from tests.unit.utils import mock_bind
from tests.unit.fixtures.guilds import GuildRoles


class MockBadges(Enum):
    """The badges available for mocking"""

    VIP_BADGE = 1
    DONATOR_BADGE = auto()


class BadgeTestFixtures(Enum):
    """The test fixtures for badge binds"""

    BADGE_BIND = "badge_bind"


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
        return mock_bind(
            mocker,
            discord_roles=find_discord_roles(discord_role),
            criteria=binds.BindCriteria(type="badge", id=badge.value),
            entity=RobloxBadge(id=badge.value),
        )

    return _get_bind_for_badge


__all__ = [
    "MockBadges",
    "BadgeTestFixtures",
] + [fixture.value for fixture in BadgeTestFixtures]
