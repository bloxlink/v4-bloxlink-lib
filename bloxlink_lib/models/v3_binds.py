from typing import Literal, Optional, Annotated
from pydantic import Field
from bloxlink_lib.models.base import BaseModel, PydanticDict

V3BindType = Literal["groups", "assets", "badges", "gamePasses"]


class V3RoleBind(BaseModel):
    """Represents a role bind for a guild in the database."""

    roles: list[str]
    nickname: Optional[str] = None
    removeRoles: list[str] = []


class V3RangeBinding(BaseModel):
    """Represents a range binding for group ranks."""

    roles: list[str]
    nickname: Optional[str] = None
    removeRoles: list[str] = []
    low: int
    high: int


class V3GroupBind(BaseModel):
    """Represents a group binding configuration."""

    binds: PydanticDict[str | Literal["all"], V3RoleBind]
    ranges: Annotated[list[V3RangeBinding], Field(default_factory=list)]
    groupName: str
    removeRoles: list[str] = []


class V3AssetBind(BaseModel):
    """Represents an asset binding configuration."""

    nickname: Optional[str] = None
    displayName: str | None = None
    removeRoles: Annotated[list[str], Field(default_factory=list)]
    roles: list[str]


class V3GroupID(BaseModel):
    """Represents a group ID configuration."""

    nickname: str
    groupName: str
    removeRoles: Annotated[list[str], Field(default_factory=list)]


class V3RoleBinds(BaseModel):
    """Represents the role binds for a guild in the database."""

    roleBinds: Annotated[
        PydanticDict[V3BindType, PydanticDict[str, V3GroupBind | V3AssetBind]],
        Field(default_factory=PydanticDict),
    ] = Field(default_factory=PydanticDict)
    groupIDs: Annotated[
        PydanticDict[str, V3GroupID], Field(default_factory=PydanticDict)
    ] = Field(default_factory=PydanticDict)


V3RoleBindType = PydanticDict[V3BindType, PydanticDict[str, V3GroupBind | V3AssetBind]]
V3GroupIDType = PydanticDict[str, V3GroupID]
