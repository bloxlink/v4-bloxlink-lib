from datetime import datetime
from typing import Mapping, Self, Sequence, Type
import discord
import hikari
from pydantic import Field, field_validator
from bloxlink_lib.models import BaseModel, Snowflake


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
    created_at: datetime = None

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
            created_at=member.created_at,
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
            created_at=member.created_at,
        )

    @staticmethod
    def user_mention(user_id: int | Snowflake | str) -> str:
        return f"<@{user_id}>"


class GuildSerializable(BaseModel):
    id: Snowflake
    name: str = None
    roles: Mapping[Snowflake, RoleSerializable] = Field(default_factory=dict)
    owner_id: Snowflake | None = None

    @field_validator("roles", mode="before")
    @classmethod
    def transform_roles(
        cls: Type[Self], roles: list[RoleSerializable | hikari.Role | dict] | dict
    ) -> Mapping[Snowflake, RoleSerializable]:
        role_type = next(iter(roles.values())) if isinstance(roles, dict) else roles[0]

        match role_type:
            case RoleSerializable():
                if isinstance(roles, dict):
                    return {Snowflake(r.id): r for r in roles.values()}

                return {Snowflake(r.id): r for r in roles}
            case dict():
                if isinstance(roles, dict):
                    return {
                        Snowflake(r["id"]): RoleSerializable(**r)
                        for r in roles.values()
                    }

                return {Snowflake(r["id"]): RoleSerializable(**r) for r in roles}
            case hikari.Role():
                return {
                    Snowflake(i): RoleSerializable.from_hikari(r)
                    for i, r in roles.items()
                }
            case _:
                raise ValueError("Invalid role type")

    @classmethod
    def from_hikari(cls, guild: hikari.RESTGuild | Self) -> "GuildSerializable":
        """Convert a Hikari guild into a GuildSerializable object."""

        if isinstance(guild, GuildSerializable):
            return guild

        return cls(
            id=guild.id, name=guild.name, roles=guild.roles, owner_id=guild.owner_id
        )
