from typing import Annotated, Any, Callable, Iterable, Literal, Self, Sequence, Type
from pydantic import BaseModel, Field, PrivateAttr, RootModel, SkipValidation, field_validator


class PydanticDict[K, V](RootModel[dict[K, V]]):
    """A Pydantic model that represents a dictionary."""

    root: dict[K, V] = Field(default_factory=dict)

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, key: K) -> V:
        return self.root[key]

    def __setitem__(self, key: K, value: V):
        self.root[key] = value

    def __delitem__(self, key: K):
        del self.root[key]

    def __contains__(self, key: K) -> bool:
        return key in self.root

    def get(self, key: K, default: V = None) -> V:
        return self.root.get(key, default)

    def pop(self, key: K, default: V = None) -> V:
        return self.root.pop(key, default)

    def keys(self):
        return self.root.keys()

    def values(self):
        return self.root.values()

    def items(self):
        return self.root.items()

    def update(self, other: dict[K, V]):
        self.root.update(other)

    def __iter__(self):
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)

    def __eq__(self, other) -> bool:
        return self.root == other.root if isinstance(other, PydanticDict) else False

    def __str__(self) -> str:
        return str(self.root)

    def __repr__(self) -> str:
        return self.__str__()


class PydanticList[T](RootModel[list[T]]):
    """A Pydantic model that represents a list."""

    root: list[T] = Field(default_factory=list)

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, index: int) -> T:
        return self.root[index]

    def __setitem__(self, index: int, value: T):
        self.root[index] = value

    def __delitem__(self, index: int):
        del self.root[index]

    def append(self, value: T):
        self.root.append(value)

    def extend(self, values: Iterable[T]):
        self.root.extend(values)

    def insert(self, index: int, value: T):
        self.root.insert(index, value)

    def remove(self, value: T):
        self.root.remove(value)

    def pop(self, index: int = -1) -> T:
        return self.root.pop(index)

    def clear(self):
        self.root.clear()

    def index(self, value: T, start: int = 0, end: int = None) -> int:
        return self.root.index(value, start, end)

    def count(self, value: T) -> int:
        return self.root.count(value)

    def sort(self, *, key: Callable[[T], Any] = None, reverse: bool = False):
        self.root.sort(key=key, reverse=reverse)

    def reverse(self):
        self.root.reverse()

    def __len__(self) -> int:
        return len(self.root)

    def __eq__(self, other) -> bool:
        return self.root == other.root if isinstance(other, PydanticList) else False

    def __str__(self) -> str:
        return str(self.root)

    def __repr__(self) -> str:
        return self.__str__()


class CoerciveSet[T: Callable](BaseModel):
    """A set that coerces the children into another type."""

    root: Annotated[Sequence[T], SkipValidation]

    @field_validator("root", mode="before", check_fields=False)
    @classmethod
    def transform_root(cls: Type[Self], old_root: Iterable[T]) -> Sequence[T]:
        return list(old_root)

    _data: set[T] = PrivateAttr(default_factory=set)

    def __init__(self, root: Iterable[T] = None):
        super().__init__(root=root or [])

    def model_post_init(self, __context: Any) -> None:
        self._data = set(self._coerce(x) for x in self.root)

    def _coerce(self, item: Any) -> T:
        target_type = self.get_type()

        if isinstance(item, target_type):
            return item
        try:
            return target_type(item)
        except (TypeError, ValueError):
            raise TypeError(f"Cannot coerce {item} to {target_type}")

    def __contains__(self, item):
        return self._data.__contains__(self._coerce(item))

    def add(self, item):
        self._data.add(self._coerce(item))

    def remove(self, item):
        self._data.remove(self._coerce(item))

    def discard(self, item):
        self._data.discard(self._coerce(item))

    def update(self, *s: Iterable[T]):
        for iterable in s:
            for item in iterable:
                self._data.add(self._coerce(item))

    def intersection(self, *s: Iterable[T]) -> 'CoerciveSet[T]':
        result = self._data.intersection(self._coerce(x) for i in s for x in i)
        return self.__class__(root=result)

    def difference(self, *s: Iterable[T]) -> 'CoerciveSet[T]':
        result = self._data.difference(self._coerce(x) for i in s for x in i)
        return self.__class__(root=result)

    def symmetric_difference(self, *s: Iterable[T]) -> 'CoerciveSet[T]':
        result = self._data.symmetric_difference(
            self._coerce(x) for i in s for x in i)
        return self.__class__(root=result)

    def union(self, *s: Iterable[T]) -> 'CoerciveSet[T]':
        result = self._data.union(self._coerce(x)
                                  for iterable in s for x in iterable)
        return self.__class__(root=result)

    def contains_all(self, iterable: Iterable[T]) -> bool:
        return all(self._coerce(x) in self._data for x in iterable)

    def contains(self, *items: Sequence[T]) -> bool:
        return all(self._coerce(x) in self._data for i in items for x in i)

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __eq__(self, other) -> bool:
        return self.contains(x for x in other) if isinstance(other, CoerciveSet) else False

    def __str__(self) -> str:
        return ", ".join(str(i) for i in self)

    def __repr__(self) -> str:
        return self.__str__()


class SnowflakeSet(CoerciveSet[int]):
    """A set of Snowflakes."""

    root: Sequence[int] = Field(kw_only=False)
    type: Literal["role", "user"] | None = Field(default=None)
    str_reference: dict = Field(default_factory=dict)

    def __init__(self, root: Iterable[int] = None, type: Literal["role", "user"] = None, str_reference: dict = None):
        super().__init__(root=root or [])
        self.type = type
        self.str_reference = str_reference or {}

    def add(self, item):
        """Add an item to the set. If the item contains an ID, it will be parsed into an integer. Otherwise, it will be added as an int."""
        if getattr(item, "id", None):
            return super().add(item.id)
        return super().add(item)

    def intersection(self, *s: Iterable[int]) -> 'SnowflakeSet':
        result = super().intersection(*s)
        return SnowflakeSet(root=result._data, type=self.type, str_reference=self.str_reference)

    def difference(self, *s: Iterable[int]) -> 'SnowflakeSet':
        result = super().difference(*s)
        return SnowflakeSet(root=result._data, type=self.type, str_reference=self.str_reference)

    def symmetric_difference(self, *s: Iterable[int]) -> 'SnowflakeSet':
        result = super().symmetric_difference(*s)
        return SnowflakeSet(root=result._data, type=self.type, str_reference=self.str_reference)

    def union(self, *s: Iterable[int]) -> 'SnowflakeSet':
        result = super().union(*s)
        return SnowflakeSet(root=result._data, type=self.type, str_reference=self.str_reference)

    def __str__(self):
        match self.type:
            case "role":
                return ", ".join(str(self.str_reference.get(i) or f"<@&{i}>") for i in self)
            case "user":
                return ", ".join(str(self.str_reference.get(i) or f"<@{i}>") for i in self)
        return ", ".join(str(self.str_reference.get(i) or i) for i in self)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._data})"
