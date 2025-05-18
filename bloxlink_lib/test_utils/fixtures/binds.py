from enum import Enum
from pydantic.dataclasses import dataclass

from bloxlink_lib.test_utils.fixtures import assets as asset_fixtures
from bloxlink_lib.test_utils.fixtures import groups as group_fixtures


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
