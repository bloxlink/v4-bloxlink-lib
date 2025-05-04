from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from enum import Enum


def filter_enum_list[T: "Enum", V](iterable: list[T]) -> list[V]:
    """Convert a list of enums to a list of their values"""

    return [e.value for e in iterable]
