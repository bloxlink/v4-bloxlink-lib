from enum import Enum, auto

__all__ = [
    "MockBadges",
]


class MockBadges(Enum):
    """The badges available for mocking"""

    VIP_BADGE = 1
    DONATOR_BADGE = auto()
