from typing import TYPE_CHECKING
from bloxlink_lib import find

if TYPE_CHECKING:
    from enum import Enum


def enum_list_to_value_list[T: "Enum", V](iterable: list[T]) -> list[V]:
    """Convert a list of enums to a list of their values"""

    return [e.value for e in iterable]
