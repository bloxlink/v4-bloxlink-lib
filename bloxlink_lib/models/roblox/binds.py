from __future__ import annotations
import math
from enum import Enum
import re
from typing import TYPE_CHECKING, Final
from hikari import Member
from bloxlink_lib.models.base.serializable import MemberSerializable, RoleSerializable
from bloxlink_lib.models.binds import (
    BindCriteria,
    GuildBind,
)
from bloxlink_lib.models.roblox.users import RobloxUser
from bloxlink_lib.models.schemas.guilds import (  # pylint: disable=no-name-in-module
    fetch_guild_data,
    update_guild_data,
)
from bloxlink_lib.utils import find

if TYPE_CHECKING:
    from bloxlink_lib.models.binds import (
        VALID_BIND_TYPES,
    )

POP_OLD_BINDS: bool = False  # remove old binds from the database
SAVE_NEW_BINDS: bool = False  # save new binds to the database

ARBITRARY_GROUP_TEMPLATE = re.compile(r"\{group-rank-(.*?)\}")

ARBITRARY_GROUP_TEMPLATE = re.compile(r"\{group-rank-(.*?)\}")
NICKNAME_TEMPLATE_REGEX = re.compile(r"\{(.*?)\}")


class RobloxUserNicknames(Enum):
    """Valid nickname templates for a Roblox user"""

    ROBLOX_NAME = "roblox-name"
    ROBLOX_ID = "roblox-id"
    ROBLOX_DISPLAY_NAME = "display-name"
    ROBLOX_AGE = "roblox-age"
    SMART_NAME = "smart-name"
    ROBLOX_CREATION_AGE = "roblox-age"
    ROBLOX_GROUP_RANK = "group-rank"


class GenericTemplates(Enum):
    """Valid templates regardless if a user has a Roblox account linked"""

    DISCORD_ID = "discord-id"
    DISCORD_NICKNAME = "discord-nick"
    DISCORD_GLOBAL_NAME = "discord-global-name"
    DISCORD_NAME = "discord-name"
    DISCORD_MENTION = "discord-mention"
    SERVER_NAME = "server-name"
    PREFIX = "prefix"
    GROUP_URL = "group-url"
    GROUP_NAME = "group-name"
    SMART_NAME = "smart-name"
    VERIFY_URL = "verify-url"


async def get_binds(
    guild_id: int | str,
    category: VALID_BIND_TYPES = None,
    bind_id: int = None,
    guild_roles: dict[int, RoleSerializable] = None,
) -> list[GuildBind]:
    """Get the current guild binds.

    Old binds will be included by default, but will not be saved in the database in the
    new format unless the POP_OLD_BINDS flag is set to True. While it is False, old formatted binds will
    be left as is.
    """

    guild_id = str(guild_id)
    guild_data = await fetch_guild_data(guild_id, "binds")

    guild_data.binds = await migrate_old_binds_to_v4(guild_id, guild_data.binds)

    if guild_roles:
        await check_for_verified_roles(
            guild_id, guild_roles=guild_roles, merge_to=guild_data.binds
        )

    return list(
        filter(
            lambda b: b.type == category
            and ((bind_id and b.criteria.id == bind_id) or not bind_id),
            guild_data.binds,
        )
        if category
        else guild_data.binds
    )


async def get_nickname_template(
    guild_id, potential_binds: list[GuildBind], roblox_user: RobloxUser | None = None
) -> tuple[str, GuildBind | None]:
    """Get the unparsed nickname template for the user."""

    guild_data = await fetch_guild_data(
        guild_id,
        "nicknameTemplate" if roblox_user else "unverifiedNickname",
    )

    # first sort the binds by role position
    potential_binds.sort(
        key=lambda b: b.highest_role.position if b.highest_role else math.inf,
        reverse=True,
    )  # arbitrary big number

    highest_priority_bind: GuildBind = potential_binds[0] if potential_binds else None

    nickname_template = (
        highest_priority_bind.nickname
        if highest_priority_bind and highest_priority_bind.nickname
        else guild_data.nicknameTemplate
    )

    return nickname_template, highest_priority_bind


async def parse_template(
    *,
    guild_id: int,
    guild_name: str,
    member: Member | MemberSerializable,
    roblox_user: RobloxUser | None = None,
    template: str = None,
    potential_binds: list[GuildBind] | None = None,
    trim_nickname=True,
) -> str | None:
    """
    Parse the template for the user.

    The algorithm is as follows:
    - Find the highest priority bind that has a nickname. The priority is determined by the position of the role in the guild.
    - If no such bind is found, the template is guild_data.nicknameTemplate.

    The template is then adjusted to the user's data.
    """

    highest_priority_bind: GuildBind | None = None
    smart_name: str = ""
    group_bind: GuildBind | None = None
    group_roleset_name: str | None = None

    if not template:
        if not guild_id or potential_binds is None:
            raise ValueError(
                "Guild ID and potential binds must be provided if no template is given."
            )

        # this is for nickname calculation
        template, highest_priority_bind = await get_nickname_template(
            guild_id, potential_binds, roblox_user
        )

    if template == "{disable-nicknaming}":
        return None

    # if the template contains a group template, sync the group
    if "group-" in template:
        # get the group from the highest bind if it's a group bind; otherwise, find the first linked group bind
        group_bind = (
            highest_priority_bind
            if highest_priority_bind and highest_priority_bind.type == "group"
            else find(lambda b: b.type == "group", potential_binds)
        )

        if group_bind:
            await group_bind.entity.sync()

    # parse {smart-name}
    if roblox_user:
        if roblox_user.display_name != roblox_user.username:
            smart_name = f"{
                roblox_user.display_name} (@{roblox_user.username})"

            if len(smart_name) > 32:
                smart_name = roblox_user.username
        else:
            smart_name = roblox_user.username

        # parse {group-rank}
        if "group-rank" in template:
            if group_bind and group_bind.criteria.id in roblox_user.groups:
                if highest_priority_bind:
                    group_roleset_name = roblox_user.groups[
                        highest_priority_bind.criteria.id
                    ].role.name
                else:
                    group_roleset_name = roblox_user.groups[
                        potential_binds[0].criteria.id
                    ].role.name
            else:
                group_roleset_name = "Guest"
        else:
            group_roleset_name = "Guest"

        # parse {group-rank-<group_id>} in the nickname template
        for group_id in ARBITRARY_GROUP_TEMPLATE.findall(template):
            group = roblox_user.groups.get(group_id)
            group_role_from_group = group.role.name if group else "Guest"

            template = template.replace(
                "{group-rank-" + group_id + "}", group_role_from_group
            )

    # parse the nickname template
    for outer_nick in NICKNAME_TEMPLATE_REGEX.findall(template):
        nick_data = outer_nick.split(":")
        nick_fn: str | None = nick_data[0] if len(nick_data) > 1 else None
        nick_value: str = nick_data[1] if len(nick_data) > 1 else nick_data[0]

        # nick_fn = capA
        # nick_value = roblox-name

        if roblox_user:
            match nick_value:
                case RobloxUserNicknames.ROBLOX_NAME.value:
                    nick_value = roblox_user.username
                case RobloxUserNicknames.ROBLOX_DISPLAY_NAME.value:
                    nick_value = roblox_user.display_name
                case RobloxUserNicknames.SMART_NAME.value:
                    nick_value = smart_name
                case RobloxUserNicknames.ROBLOX_ID.value:
                    nick_value = str(roblox_user.id)
                case RobloxUserNicknames.ROBLOX_AGE.value:
                    nick_value = str(roblox_user.age_days)
                case RobloxUserNicknames.ROBLOX_GROUP_RANK.value:
                    nick_value = group_roleset_name or "Guest"

        if member:
            match nick_value:
                case GenericTemplates.DISCORD_NAME.value:
                    nick_value = member.username
                case GenericTemplates.DISCORD_NICKNAME.value:
                    nick_value = member.nickname if member.nickname else member.username
                case GenericTemplates.DISCORD_GLOBAL_NAME.value:
                    nick_value = (
                        member.global_name if member.global_name else member.username
                    )
                case GenericTemplates.DISCORD_MENTION.value:
                    nick_value = member.mention
                case GenericTemplates.DISCORD_ID.value:
                    nick_value = str(member.id)
                case GenericTemplates.SERVER_NAME.value:
                    nick_value = guild_name
                case GenericTemplates.PREFIX.value:
                    nick_value = "/"
                case GenericTemplates.GROUP_URL.value:
                    nick_value = group_bind.entity.url if group_bind else ""
                case GenericTemplates.GROUP_NAME.value:
                    nick_value = group_bind.entity.name if group_bind else ""
                case GenericTemplates.SMART_NAME.value:
                    nick_value = smart_name
                case GenericTemplates.VERIFY_URL.value:
                    nick_value = "https://blox.link/verify"

        if nick_fn:
            if nick_fn in ("allC", "allL"):
                if nick_fn == "allC":
                    nick_value = nick_value.upper()
                elif nick_fn == "allL":
                    nick_value = nick_value.lower()

                template = template.replace("{{{0}}}".format(outer_nick), nick_value)
            else:
                template = template.replace(
                    "{{{0}}}".format(outer_nick), outer_nick
                )  # remove {} only
        else:
            template = template.replace("{{{0}}}".format(outer_nick), nick_value)

    if trim_nickname:
        return template[:32]

    return template


async def migrate_old_binds_to_v4(
    guild_id: str, binds: list[GuildBind]
) -> list[GuildBind]:
    """Migrates binds from the V3 structure to V4 and optionally saves them to the database.

    If POP_OLD_BINDS is true, the old binds will be removed from the database.
    """

    guild_data = await fetch_guild_data(
        guild_id,
        "roleBinds",
        "groupIDs",
        "migratedBindsToV4",
    )

    new_migrated_binds: list[GuildBind] = []

    if not guild_data.migratedBindsToV4 and (
        guild_data.roleBinds or guild_data.groupIDs
    ):
        new_migrated_binds = GuildBind.from_V3(guild_data)

    if new_migrated_binds:
        # Remove duplicates
        binds.extend(b for b in new_migrated_binds if b not in binds)

        if SAVE_NEW_BINDS:
            await update_guild_data(
                guild_id,
                binds=[b.model_dump(exclude_unset=True, by_alias=True) for b in binds],
                migratedBindsToV4=True,
            )

    # if POP_OLD_BINDS, remove v3 binds from the database
    if POP_OLD_BINDS and guild_data.migratedBindsToV4:
        await update_guild_data(
            guild_id, groupIDs=None, roleBinds=None, migratedBindsToV4=None
        )
        return binds

    return binds


async def check_for_verified_roles(
    guild_id: int | str,
    guild_roles: dict[int, RoleSerializable],
    merge_to: list[GuildBind],
):
    """Check for existing verified/unverified roles and update the database."""

    guild_id = str(guild_id)
    guild_data = await fetch_guild_data(
        guild_id,
        "verifiedRole",
        "unverifiedRole",
        "verifiedRoleName",
        "unverifiedRoleName",
        "unverifiedRoleEnabled",
    )

    verified_role_name = guild_data.verifiedRoleName
    unverified_role_name = guild_data.unverifiedRoleName
    verified_role_enabled = guild_data.verifiedRoleEnabled
    unverified_role_enabled = guild_data.unverifiedRoleEnabled
    verified_role_id = guild_data.verifiedRole
    unverified_role_id = guild_data.unverifiedRole

    new_verified_binds: list[GuildBind] = []

    if verified_role_enabled and not find(
        lambda b: b.criteria.type == "verified", merge_to
    ):
        verified_role = find(
            lambda r: str(r.id) == verified_role_id or r.name == verified_role_name,
            guild_roles.values(),
        )

        if verified_role:
            new_bind = GuildBind(
                criteria=BindCriteria(type="verified"),
                roles=[str(verified_role.id)],
            )
            new_verified_binds.append(new_bind)

    if unverified_role_enabled and not find(
        lambda b: b.criteria.type == "unverified", merge_to
    ):
        unverified_role = find(
            lambda r: str(r.id) == unverified_role_id or r.name == unverified_role_name,
            guild_roles.values(),
        )

        if unverified_role:
            new_bind = GuildBind(
                criteria=BindCriteria(type="unverified"),
                roles=[str(unverified_role.id)],
            )
            new_verified_binds.append(new_bind)

    if new_verified_binds:
        merge_to.extend(new_verified_binds)

        await update_guild_data(
            guild_id,
            binds=[b.model_dump(exclude_unset=True, by_alias=True) for b in merge_to],
            verifiedRoleName=None,
            unverifiedRoleName=None,
        )


async def count_binds(guild_id: int | str, bind_id: int = None) -> int:
    """Count the number of binds that this guild_id has created.

    Args:
        guild_id (int | str): ID of the guild.
        bind_id (int, optional): ID of the entity to filter by when counting. Defaults to None.

    Returns:
        int: The number of bindings this guild has created.
    """

    guild_data = await get_binds(guild_id)

    return (
        len(guild_data)
        if not bind_id
        else sum(1 for b in guild_data if b.id == int(bind_id)) or 0
    )
