from datetime import datetime
from typing import (
    Callable,
    Iterable,
    Mapping,
    Type,
    Any,
    Literal,
    Annotated,
    Tuple,
    Sequence,
    Self,
)
from abc import ABC, abstractmethod
from pydantic import (
    BaseModel as PydanticBaseModel,
    BeforeValidator,
    WithJsonSchema,
    ConfigDict,
    Field,
    SkipValidation,
    PrivateAttr,
    field_validator,
    RootModel,
)
from pydantic.fields import FieldInfo
from generics import get_filled_type
import hikari
import discord

Snowflake = Annotated[int, BeforeValidator(int), WithJsonSchema({"type": "int"})]


class UNDEFINED:
    """
    Can be used to differentiate between None and undefined
    in function arguments.
    """


class BaseModelArbitraryTypes(PydanticBaseModel):
    """Base model with arbitrary types allowed."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True, populate_by_name=True, validate_assignment=True
    )


class BaseModel(PydanticBaseModel):
    """Base model with a set configuration."""

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)
    _generic_type_value: Any = None

    @classmethod
    def model_fields_index(
        cls: Type[PydanticBaseModel | BaseModelArbitraryTypes],
    ) -> list[Tuple[str, FieldInfo]]:
        """Returns a list of the model's fields with the name as a tuple.

        Useful if the field index is necessary.

        """

        fields_with_names: list[Tuple[str, FieldInfo]] = []

        for field_name, field in cls.model_fields.items():
            fields_with_names.append((field_name, field))

        return fields_with_names

    def get_type(self) -> Any:
        if self._generic_type_value:
            return self._generic_type_value

        try:
            self._generic_type_value = get_filled_type(self, BaseModel, 0)
        except TypeError:
            pass

        return self._generic_type_value


class PydanticDict[K, V](RootModel[dict[K, V]]):
    """A Pydantic model that represents a dictionary."""

    root: Annotated[dict[K, V], Field(default_factory=dict)]

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

    root: Annotated[list[T], Field(default_factory=list)]

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


class RobloxEntity(BaseModel, ABC):
    """Representation of an entity on Roblox.

    Attributes:
        id(str): Roblox given ID of the entity.
        name(str, optional): Name of the entity.
        description(str, optional): The description of the entity(if any).
        synced(bool): If this entity has been synced with Roblox or not . False by default.
    """

    id: int | None
    name: str = None
    description: str | None = None
    synced: bool = False
    url: str = None

    @abstractmethod
    async def sync(self):
        """Sync a Roblox entity with the data from Roblox."""
        raise NotImplementedError()

    def __str__(self) -> str:
        name = f"**{self.name}**" if self.name else "*(Unknown Roblox Entity)*"
        return f"{name} ({self.id})"


class BloxlinkEntity(RobloxEntity):
    """Entity for Bloxlink-specific operations."""

    type: Literal["verified", "unverified"]
    id: None = None

    async def sync(self):
        pass

    def __str__(self) -> str:
        return "Verified Users" if self.type == "verified" else "Unverified Users"


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

    def intersection(self, *s: Iterable[T]) -> "CoerciveSet[T]":
        result = self._data.intersection(self._coerce(x) for i in s for x in i)
        return self.__class__(root=result)

    def difference(self, *s: Iterable[T]) -> "CoerciveSet[T]":
        result = self._data.difference(self._coerce(x) for i in s for x in i)
        return self.__class__(root=result)

    def symmetric_difference(self, *s: Iterable[T]) -> "CoerciveSet[T]":
        result = self._data.symmetric_difference(self._coerce(x) for i in s for x in i)
        return self.__class__(root=result)

    def union(self, *s: Iterable[T]) -> "CoerciveSet[T]":
        result = self._data.union(self._coerce(x) for iterable in s for x in iterable)
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
        return (
            self.contains(x for x in other) if isinstance(other, CoerciveSet) else False
        )

    def __str__(self) -> str:
        return ", ".join(str(i) for i in self)

    def __repr__(self) -> str:
        return self.__str__()


class SnowflakeSet(CoerciveSet[int]):
    """A set of Snowflakes."""

    root: Sequence[int] = Field(kw_only=False)
    type: Literal["role", "user"] | None = Field(default=None)
    str_reference: dict = Field(default_factory=dict)

    def __init__(
        self,
        root: Iterable[int] = None,
        type: Literal["role", "user"] = None,
        str_reference: dict = None,
    ):
        super().__init__(root=root or [])
        self.type = type
        self.str_reference = str_reference or {}

    def add(self, item):
        """Add an item to the set. If the item contains an ID, it will be parsed into an integer. Otherwise, it will be added as an int."""
        if getattr(item, "id", None):
            return super().add(item.id)
        return super().add(item)

    def intersection(self, *s: Iterable[int]) -> "SnowflakeSet":
        result = super().intersection(*s)
        return SnowflakeSet(
            root=result._data, type=self.type, str_reference=self.str_reference
        )

    def difference(self, *s: Iterable[int]) -> "SnowflakeSet":
        result = super().difference(*s)
        return SnowflakeSet(
            root=result._data, type=self.type, str_reference=self.str_reference
        )

    def symmetric_difference(self, *s: Iterable[int]) -> "SnowflakeSet":
        result = super().symmetric_difference(*s)
        return SnowflakeSet(
            root=result._data, type=self.type, str_reference=self.str_reference
        )

    def union(self, *s: Iterable[int]) -> "SnowflakeSet":
        result = super().union(*s)
        return SnowflakeSet(
            root=result._data, type=self.type, str_reference=self.str_reference
        )

    def __str__(self):
        match self.type:
            case "role":
                return ", ".join(
                    str(self.str_reference.get(i) or f"<@&{i}>") for i in self
                )
            case "user":
                return ", ".join(
                    str(self.str_reference.get(i) or f"<@{i}>") for i in self
                )
        return ", ".join(str(self.str_reference.get(i) or i) for i in self)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._data})"


class RoleSerializable(BaseModel):
    id: Snowflake
    name: str = None
    color: int = None
    is_hoisted: bool = None
    position: int = None
    permissions: Snowflake = None
    is_managed: bool = None
    is_mentionable: bool = None

    @classmethod
    def from_hikari(cls, role: hikari.Role | Self) -> "RoleSerializable":
        """Convert a Hikari role into a RoleSerializable object."""

        if isinstance(role, RoleSerializable):
            return role

        return cls(
            id=role.id,
            name=role.name,
            color=role.color,
            is_hoisted=role.is_hoisted,
            position=role.position,
            permissions=role.permissions,
            is_managed=role.is_managed,
            is_mentionable=role.is_mentionable,
        )

    @staticmethod
    def role_mention(role_id: int | Snowflake | str) -> str:
        return f"<@&{role_id}>"


class MemberSerializable(BaseModel):
    id: Snowflake
    username: str = None
    avatar_url: str = None
    display_name: str = None
    global_name: str | None = None
    is_bot: bool = None
    joined_at: datetime = None
    role_ids: Sequence[Snowflake] = None
    guild_id: int | None = None
    nickname: str | None = None
    mention: str = None

    @classmethod
    def from_hikari(
        cls, member: hikari.InteractionMember | Self
    ) -> "MemberSerializable":
        """Convert a Hikari member into a MemberSerializable object."""

        if isinstance(member, MemberSerializable):
            return member

        return cls(
            id=member.id,
            username=member.username,
            avatar_url=str(member.avatar_url),
            global_name=member.global_name,
            display_name=member.display_name,
            is_bot=member.is_bot,
            joined_at=member.joined_at,
            role_ids=member.role_ids,
            guild_id=member.guild_id,
            nickname=member.nickname,
            mention=member.mention,
        )

    @classmethod
    def from_discordpy(cls, member: discord.Member | Self) -> "MemberSerializable":
        """Convert a Discord.py member into a MemberSerializable object."""

        if isinstance(member, MemberSerializable):
            return member

        return cls(
            id=member.id,
            username=member.name,
            avatar_url=member.display_avatar.url,
            global_name=member.global_name,
            display_name=member.display_name,
            is_bot=member.bot,
            joined_at=member.joined_at,
            role_ids=[role.id for role in member.roles],
            guild_id=member.guild.id,
            nickname=member.nick,
            mention=member.mention,
        )

    @staticmethod
    def user_mention(user_id: int | Snowflake | str) -> str:
        return f"<@{user_id}>"


class GuildSerializable(BaseModel):
    id: Snowflake
    name: str = None
    roles: Mapping[Snowflake, RoleSerializable] = Field(default_factory=dict)

    @field_validator("roles", mode="before")
    @classmethod
    def transform_roles(
        cls: Type[Self], roles: list
    ) -> Mapping[Snowflake, RoleSerializable]:
        return {int(r_id): RoleSerializable.from_hikari(r) for r_id, r in roles.items()}

    @classmethod
    def from_hikari(cls, guild: hikari.RESTGuild | Self) -> "GuildSerializable":
        """Convert a Hikari guild into a GuildSerializable object."""

        if isinstance(guild, GuildSerializable):
            return guild

        return cls(id=guild.id, name=guild.name, roles=guild.roles)


def create_entity(
    category: (
        Literal["asset", "badge", "gamepass", "group", "verified", "unverified"] | str
    ),
    entity_id: int,
) -> RobloxEntity | None:
    """Create a respective Roblox entity from a category and ID.

    Args:
        category(str): Type of Roblox entity to make. Subset from asset, badge, group, gamepass.
        entity_id(int): ID of the entity on Roblox.

    Returns:
        RobloxEntity: The respective RobloxEntity implementer, unsynced, or None if the category is invalid.
    """

    match category:
        case "asset":
            from bloxlink_lib.models import (
                assets,
            )  # pylint: disable=import-outside-toplevel

            return assets.RobloxAsset(id=entity_id)

        case "badge":
            from bloxlink_lib.models import (
                badges,
            )  # pylint: disable=import-outside-toplevel

            return badges.RobloxBadge(id=entity_id)

        case "gamepass":
            from bloxlink_lib.models import (
                gamepasses,
            )  # pylint: disable=import-outside-toplevel

            return gamepasses.RobloxGamepass(id=entity_id)

        case "group":
            from bloxlink_lib.models import (
                groups,
            )  # pylint: disable=import-outside-toplevel

            return groups.RobloxGroup(id=entity_id)

        case "verified" | "unverified":
            return BloxlinkEntity(type=category)

    return None


async def get_entity(
    category: Literal["asset", "badge", "gamepass", "group"] | str, entity_id: int
) -> RobloxEntity:
    """Get and sync a Roblox entity.

    Args:
        category(str): Type of Roblox entity to get. Subset from asset, badge, group, gamepass.
        entity_id(int): ID of the entity on Roblox.

    Returns:
        RobloxEntity: The respective RobloxEntity implementer, synced.
    """

    entity = create_entity(category, int(entity_id))

    await entity.sync()

    return entity
