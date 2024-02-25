from __future__ import annotations
from typing import Any, Literal, TYPE_CHECKING, TypedDict, NotRequired
import re

from pydantic import Field, ValidationError

from ..models.base import RobloxEntity, create_entity, BaseModel, SnowflakeSet, CoerciveSet
import bloxlink_lib.database as database
from ..utils import find

if TYPE_CHECKING:
    from .guilds import RoleSerializable
    from .users import MemberSerializable, RobloxUser
    from .groups import RobloxGroup
    from .assets import RobloxAsset
    from hikari import Member

POP_OLD_BINDS: bool = False

VALID_BIND_TYPES = Literal["group", "catalogAsset", "badge", "gamepass", "verified", "unverified"]
ARBITRARY_GROUP_TEMPLATE = re.compile(r"\{group-rank-(.*?)\}")
NICKNAME_TEMPLATE_REGEX = re.compile(r"\{(.*?)\}")


# TypedDict definitions used for function kwargs
class GroupBindDataDict(TypedDict, total=False):
    everyone: bool
    guest: bool
    min: int
    max: int
    roleset: int
    dynamicRoles: bool

class BindCriteriaDict(TypedDict):
    type: VALID_BIND_TYPES
    id: NotRequired[int]
    group: NotRequired[GroupBindData]

class BindDataDict(TypedDict):
    displayName: str


# Pydantic definitions
class GroupBindData(BaseModel):
    """Represents the data required for a group bind."""

    # conditions
    everyone: bool = False
    guest: bool = False
    min: int = None
    max: int = None
    roleset: int = None
    ####################

    dynamicRoles: bool = False # full group bind

    def model_post_init(self, __context: Any) -> None:
        if (self.min or self.max) and not all([self.min, self.max]):
            raise ValidationError("Both min and max range must be set.")

        if self.roleset and (self.min or self.max):
            raise ValidationError("Either a Roleset or range can be set.")

        if self.everyone and (self.guest or self.min or self.max or self.roleset):
            raise ValidationError("Everyone condition cannot have any other conditions.")

class BindCriteria(BaseModel):
    """Represents the criteria required for a bind. If anything is set, it must ALL be met."""

    type: VALID_BIND_TYPES
    id: int | None = Field(default=None)

    group: GroupBindData | None = None


class BindData(BaseModel):
    """Represents the data required for a bind."""

    displayName: str = None


class GuildBind(BaseModel):
    """Represents a role binding from the database.

    Attributes:
        nickname (str, optional): The nickname template to be applied to users. Defaults to None.
        roles (list): The IDs of roles that should be given by this bind.
        removeRole (list): The IDs of roles that should be removed when this bind is given.

        criteria (BindCriteria): Bind-specific requirements

        entity (RobloxEntity, optional): The entity that this binding represents. Defaults to None.
    """

    # Fields from the database.
    nickname: str | None = None
    roles: list[str] = Field(default_factory=list)
    remove_roles: list[str] = Field(default_factory=list, alias="removeRoles")

    criteria: BindCriteria
    data: BindData | None = Field(default=None)

    # Excluded fields. These are used for the bind algorithms.
    entity: RobloxEntity | None = Field(exclude=True, default=None)
    type: Literal["group", "catalogAsset", "badge", "gamepass", "verified", "unverified"] | None = Field(exclude=True, default=None)
    subtype: Literal["role_bind", "full_group"] | None = Field(exclude=True, default=None)
    highest_role: RoleSerializable | None = Field(exclude=True, default=None) # highest role in the guild

    def model_post_init(self, __context):
        self.entity = self.entity or create_entity(self.criteria.type, self.criteria.id)
        self.type = self.criteria.type

        if self.type == "group":
            self.subtype = "full_group" if self.criteria.group.dynamicRoles else "role_bind"

    def calculate_highest_role(self, guild_roles: dict[str, RoleSerializable]) -> None:
        """Calculate the highest role in the guild for this bind."""

        if self.roles and not self.highest_role:
            filtered_binds = filter(lambda r: str(r.id) in self.roles and self.nickname, guild_roles.values()) # pylint: disable=unsupported-membership-test

            if len(list(filtered_binds)):
                self.highest_role = max(filtered_binds, key=lambda r: r.position)

    async def satisfies_for(self, guild_roles: dict[int, RoleSerializable], member: Member | MemberSerializable, roblox_user: RobloxUser | None = None) -> tuple[bool, SnowflakeSet, CoerciveSet[str], SnowflakeSet]:
        """Check if a user satisfies the requirements for this bind."""

        ineligible_roles = SnowflakeSet()
        additional_roles = SnowflakeSet()
        missing_roles = CoerciveSet(str)

        if not roblox_user:
            if self.criteria.type == "unverified":
                return True, additional_roles, missing_roles, ineligible_roles

            # user is unverified, so remove Verified role
            if self.criteria.type == "verified":
                for role_id in filter(lambda r: int(r) in member.role_ids, self.roles):
                    ineligible_roles.add(role_id)

            return False, additional_roles, missing_roles, ineligible_roles


        # user is verified
        match self.criteria.type:
            case "verified":
                return True, additional_roles, missing_roles, ineligible_roles

            case "group":
                group: RobloxGroup = self.entity

                await roblox_user.sync(["groups"])

                if self.criteria.id in roblox_user.groups:
                    # full group bind. check for a matching roleset
                    if self.criteria.group.dynamicRoles:
                        await group.sync_for(roblox_user)

                        user_roleset = group.user_roleset
                        roleset_role = find(lambda r: r.name == user_roleset.name, guild_roles.values())

                        if roleset_role:
                            additional_roles.add(roleset_role.id)
                        else:
                            missing_roles.add(user_roleset.name)

                    if self.criteria.group.everyone:
                        return True, additional_roles, missing_roles, ineligible_roles

                    if self.criteria.group.guest:
                        return False, additional_roles, missing_roles, ineligible_roles

                    await group.sync_for(roblox_user)

                    if (self.criteria.group.min and self.criteria.group.max) and (self.criteria.group.min <= group.user_roleset.rank <= self.criteria.group.max):
                        return True, additional_roles, missing_roles, ineligible_roles

                    if self.criteria.group.roleset:
                        roleset = self.criteria.group.roleset
                        return group.user_roleset.rank == roleset or (roleset < 0 and group.user_roleset.rank <= abs(roleset)), additional_roles, missing_roles, ineligible_roles

                    return True, additional_roles, missing_roles, ineligible_roles


                # Not in group.
                # check if the user has any group rolesets they shouldn't have
                if self.criteria.group.dynamicRoles:
                    await group.sync()

                    for roleset in group.rolesets.values():
                        for role_id in member.role_ids:
                            if role_id in guild_roles and guild_roles[role_id].name == roleset.name:
                                ineligible_roles.add(role_id)

                # Return whether the bind is for guests only
                return self.criteria.group.guest, additional_roles, missing_roles, ineligible_roles

            case "badge" | "gamepass" | "catalogAsset":
                asset: RobloxAsset = self.entity

                return await roblox_user.owns_asset(asset), additional_roles, missing_roles, ineligible_roles


        return False, additional_roles, missing_roles, ineligible_roles

    @property
    def description_prefix(self) -> str:
        """Generate the prefix string for a bind's description.

        Returns:
            str: The prefix string for a bind's description.
        """

        match self.type:
            case "group":
                if self.criteria.group.min and self.criteria.group.max:
                    return "People with a rank between"

                if self.criteria.group.min and self.criteria.group.max:
                    return "People with a rank in-between the range"

                if self.criteria.group.roleset:
                    if self.criteria.group.roleset < 0:
                        return "People with a rank greater than or equal to"

                    return "People with the rank"

                if self.criteria.group.guest:
                    return "People who are NOT in **this group**"

                if self.criteria.group.everyone:
                    return "People who are in **this group**"

            case "verified":
                return "People who have verified their Roblox account"

            case "unverified":
                return "People who have not verified their Roblox account"

            case _:
                return f"People who own the {self.type}"

    @property
    def description_content(self) -> str:
        """Generate the content string for a bind's description.

        This will be the content that describes the rolesets to be given,
        or the name of the other entity that the bind is for.

        Returns:
            str: The content string for a bind's description.
                Roleset bindings like guest and everyone do not have content to display,
                as the given prefix string contains the content.
        """

        content: str = None

        match self.type:
            case "group":
                group: RobloxGroup = self.entity

                if self.criteria.group.min and self.criteria.group.max:
                    content = f"{group.roleset_name_string(self.criteria.group.min, bold_name=False)} to {group.roleset_name_string(self.criteria.group.max, bold_name=False)}"

                elif self.criteria.group.roleset:
                    content = group.roleset_name_string(abs(self.criteria.group.roleset), bold_name=False)

            case "verified" | "unverified":
                content = ""

            case _:
                content = str(self.entity).replace("**", "")

        return content

    @property
    def short_description(self) -> str:
        """Similar to str() but does not give details about the roles"""

        if self.type == "group" and self.subtype == "full_group":
            return "All users receive a role matching their group rank name"

        content = self.description_content

        return (
            f"{self.description_prefix}{' ' if content else ''}{f'**{content}** ' if content else ''}"
        )

    def __str__(self) -> str:
        """Builds a sentence-formatted string for a binding.

        Results in the layout of: <USERS> <CONTENT ID/RANK> receive the role(s) <ROLE LIST>, and have the roles
        removed <REMOVE ROLE LIST>

        The remove role list is only appended if it there are roles to remove.

        Example output:
            All users in this group receive the role matching their group rank name.
            People with the rank Developers (200) receive the role @a
            People with a rank greater than or equal to Supporter (1) receive the role @b

        Returns:
            str: The sentence description of this binding.
        """

        extended_description = self.short_description

        if self.type == "group" and self.subtype == "full_group":
            return "- _All users in **this** group receive the role matching their group rank name_" # extended_description is not used in case we want the description to be shorter

        role_mentions = ", ".join(f"<@&{val}>" for val in self.roles)
        remove_role_mentions = ", ".join(f"<@&{val}>" for val in self.remove_roles)

        return (
            f"- _{extended_description} receive the "
            f"role{'s' if len(self.roles) > 1  else ''} {role_mentions}"
            f"{'' if len(self.remove_roles) == 0 else f', and have these roles removed: {remove_role_mentions}'}_"
        )

    def __eq__(self, other: GuildBind) -> bool:
        return self.criteria == other.criteria

async def build_binds_desc(
    guild_id: int | str,
    bind_id: int | str = None,
    bind_type: VALID_BIND_TYPES = None,
) -> str:
    """Get a string-based representation of all bindings (matching the bind_id and bind_type).

    Output is limited to 5 bindings, after that the user is told to visit the website to see the rest.

    Args:
        guild_id (int | str): ID of the guild.
        bind_id (int | str, optional): The entity ID to filter binds from. Defaults to None.
        bind_type (ValidBindType, optional): The type of bind to filter the response by.
            Defaults to None.

    Returns:
        str: Sentence representation of the first five binds matching the filters.
    """

    guild_binds = await get_binds(guild_id, category=bind_type, bind_id=bind_id)

    # sync the first 5 binds
    for bind in guild_binds[:5]:
        await bind.entity.sync()

    bind_strings = [str(bind) for bind in guild_binds[:5]]
    output = "\n".join(bind_strings)

    if len(guild_binds) > 5:
        output += (
            f"\n_... and {len(guild_binds) - 5} more. "
            f"Click [here](https://www.blox.link/dashboard/guilds/{guild_id}/binds) to view the rest!_"
        )
    return output

async def count_binds(guild_id: int | str, bind_id: int = None) -> int:
    """Count the number of binds that this guild_id has created.

    Args:
        guild_id (int | str): ID of the guild.
        bind_id (int, optional): ID of the entity to filter by when counting. Defaults to None.

    Returns:
        int: The number of bindings this guild has created.
    """

    guild_data = await get_binds(guild_id)

    return len(guild_data) if not bind_id else sum(1 for b in guild_data if b.id == int(bind_id)) or 0

async def get_binds(guild_id: int | str, category: VALID_BIND_TYPES = None, bind_id: int = None, guild_roles: dict[int, RoleSerializable] = None) -> list[GuildBind]:
    """Get the current guild binds.

    Old binds will be included by default, but will not be saved in the database in the
    new format unless the POP_OLD_BINDS flag is set to True. While it is False, old formatted binds will
    be left as is.
    """

    guild_id = str(guild_id)
    guild_data = await database.fetch_guild_data(guild_id, "binds", "verifiedRole", "unverifiedRole", "verifiedRoleName", "unverifiedRoleName", "unverifiedRoleEnabled", "unverifiedRoleEnabled") # some are needed to polyfill the binds

    # check the guild roles for a verified role
    if guild_roles and (guild_data.unverifiedRoleEnabled or guild_data.verifiedRoleEnabled) and not any(b.criteria.type == "verified" for b in guild_data.binds):
        verified_role_name = guild_data.verifiedRoleName
        unverified_role_name = guild_data.unverifiedRoleName
        verified_role_enabled = guild_data.verifiedRoleEnabled
        unverified_role_enabled = guild_data.unverifiedRoleEnabled

        if verified_role_name or unverified_role_name:
            for role in guild_roles.values():
                if verified_role_enabled and role.name == verified_role_name:
                    guild_data.binds.append(GuildBind(
                        criteria=BindCriteria(type="verified"),
                        roles=[str(role.id)],
                    ))
                elif unverified_role_enabled and role.name == unverified_role_name:
                    guild_data.binds.append(GuildBind(
                        criteria=BindCriteria(type="unverified"),
                        roles=[str(role.id)],
                    ))

    return list(filter(lambda b: b.type == category and ((bind_id and b.criteria.id == bind_id) or not bind_id), guild_data.binds) if category else guild_data.binds)

    # Convert and save old bindings in the new format
    # if not guild_data.converted_binds and (
    #     guild_data.groupIDs is not None or guild_data.roleBinds is not None
    # ):
    #     old_binds = []

    #     if guild_data.groupIDs:
    #         old_binds.extend(convert_v3_binds_to_v4(guild_data.groupIDs, "group"))

    #     if guild_data.roleBinds:
    #         gamepasses = guild_data.roleBinds.get("gamePasses")
    #         if gamepasses:
    #             old_binds.extend(convert_v3_binds_to_v4(gamepasses, "gamepass"))

    #         assets = guild_data.roleBinds.get("assets")
    #         if assets:
    #             old_binds.extend(convert_v3_binds_to_v4(assets, "asset"))

    #         badges = guild_data.roleBinds.get("badges")
    #         if badges:
    #             old_binds.extend(convert_v3_binds_to_v4(badges, "badge"))

    #         group_ranks = guild_data.roleBinds.get("groups")
    #         if group_ranks:
    #             old_binds.extend(convert_v3_binds_to_v4(group_ranks, "group"))

    #     if old_binds:
    #         # Prevent duplicates from being made. Can't use sets because dicts aren't hashable
    #         guild_data.binds.extend(bind for bind in old_binds if bind not in guild_data.binds)

    #         await update_guild_data(guild_id, binds=guild_data.binds, converted_binds=True)
    #         guild_data.converted_binds = True

    # if POP_OLD_BINDS and guild_data.converted_binds:
    #     await update_guild_data(guild_id, groupIDs=None, roleBinds=None, converted_binds=None)

    # return [
    #     GuildBind(**bind) for bind in guild_data.binds
    # ]


async def get_nickname_template(guild_id, potential_binds: list[GuildBind]) -> tuple[str, GuildBind | None]:
    """Get the unparsed nickname template for the user."""

    guild_data = await database.fetch_guild_data(
        guild_id,
        "nicknameTemplate",
    )

    # first sort the binds by role position
    potential_binds.sort(key=lambda b: b.highest_role.position if b.highest_role else 100000, reverse=True) # arbitrary big number

    highest_priority_bind: GuildBind = potential_binds[0] if potential_binds else None

    nickname_template = highest_priority_bind.nickname if highest_priority_bind and highest_priority_bind.nickname else guild_data.nicknameTemplate

    return nickname_template, highest_priority_bind


async def parse_template(guild_id: int, guild_name: str, member: Member | MemberSerializable, template: str = None, potential_binds: list[GuildBind] | None = None, roblox_user: RobloxUser | None = None, max_length=True) -> str | None:
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

    if not template:
        if not guild_id or potential_binds is None:
            raise ValueError("Guild ID and potential binds must be provided if no template is given.")

        # this is for nickname calculation
        template, highest_priority_bind = await get_nickname_template(guild_id, potential_binds)

    if template == "{disable-nicknaming}":
        return None

    # if the template contains a group template, sync the group
    if "group-" in template:
        # get the group from the highest bind if it's a group bind; otherwise, find the first linked group bind
        group_bind = highest_priority_bind if highest_priority_bind and highest_priority_bind.type == "group" else find(lambda b: b.type == "group", potential_binds)

        if group_bind:
            await group_bind.entity.sync()

    # parse {smart-name}
    if roblox_user:
        if roblox_user.display_name != roblox_user.username:
            smart_name = f"{roblox_user.display_name} (@{roblox_user.username})"

            if len(smart_name) > 32:
                smart_name = roblox_user.username
        else:
            smart_name = roblox_user.username

        # parse {group-rank}
        if roblox_user:
            if "group-rank" in template:
                if group_bind and group_bind.criteria.id in roblox_user.groups:
                    if highest_priority_bind:
                        group_roleset_name = roblox_user.groups[highest_priority_bind.criteria.id].role.name
                    else:
                        group_roleset_name = roblox_user.groups[potential_binds[0].criteria.id].role.name
                else:
                    group_roleset_name = "Guest"
            else:
                group_roleset_name = "Guest"

            # parse {group-rank-<group_id>} in the nickname template
            for group_id in ARBITRARY_GROUP_TEMPLATE.findall(template):
                group = roblox_user.groups.get(group_id)
                group_role_from_group = group.role.name if group else "Guest"

                template = template.replace("{group-rank-"+group_id+"}", group_role_from_group)

    # parse the nickname template
    for outer_nick in NICKNAME_TEMPLATE_REGEX.findall(template):
        nick_data = outer_nick.split(":")
        nick_fn: str | None = nick_data[0] if len(nick_data) > 1 else None
        nick_value: str = nick_data[1] if len(nick_data) > 1 else nick_data[0]

        # nick_fn = capA
        # nick_value = roblox-name

        if roblox_user:
            match nick_value:
                case "roblox-name":
                    nick_value = roblox_user.username
                case "display-name":
                    nick_value = roblox_user.display_name
                case "smart-name":
                    nick_value = smart_name
                case "roblox-id":
                    nick_value = str(roblox_user.id)
                case "roblox-age":
                    nick_value = str(roblox_user.age_days)
                case "group-rank":
                    nick_value = group_roleset_name

        match nick_value:
            case "discord-name":
                nick_value = member.username
            case "discord-nick":
                nick_value = member.nickname if member.nickname else member.username
            case "discord-mention":
                nick_value = member.mention
            case "discord-id":
                nick_value = str(member.id)
            case "server-name":
                nick_value = guild_name
            case "prefix":
                nick_value = "/"
            case "group-url":
                nick_value = group_bind.entity.url if group_bind else ""
            case "group-name":
                nick_value = group_bind.entity.name if group_bind else ""
            case "smart-name":
                nick_value = smart_name
            case "verify-url":
                nick_value = "https://blox.link/verify"

        if nick_fn:
            if nick_fn in ("allC", "allL"):
                if nick_fn == "allC":
                    nick_value = nick_value.upper()
                elif nick_fn == "allL":
                    nick_value = nick_value.lower()

                template = template.replace("{{{0}}}".format(outer_nick), nick_value)
            else:
                template = template.replace("{{{0}}}".format(outer_nick), outer_nick) # remove {} only
        else:
            template = template.replace("{{{0}}}".format(outer_nick), nick_value)

    if max_length:
        return template[:32]

    return template

# def convert_v3_binds_to_v4(items: dict, bind_type: str) -> list:
#     """Convert old bindings to the new bind format.

#     Args:
#         items (dict): The bindings to convert.
#         bind_type (ValidBindType): Type of bind that is being made.

#     Returns:
#         list: The binds in the new format.
#     """
#     output = []

#     for bind_id, data in items.items():
#         group_rank_binding = data.get("binds") or data.get("ranges")

#         if bind_type != "group" or not group_rank_binding:
#             bind_data = {
#                 "roles": data.get("roles"),
#                 "removeRoles": data.get("removeRoles"),
#                 "nickname": data.get("nickname"),
#                 "bind": {"type": bind_type, "id": int(bind_id)},
#             }
#             output.append(bind_data)
#             continue

#         # group rank bindings
#         if data.get("binds"):
#             for rank_id, sub_data in data["binds"].items():
#                 bind_data = {}

#                 bind_data["bind"] = {"type": bind_type, "id": int(bind_id)}
#                 bind_data["roles"] = sub_data.get("roles")
#                 bind_data["nickname"] = sub_data.get("nickname")
#                 bind_data["removeRoles"] = sub_data.get("removeRoles")

#                 # Convert to an int if possible beforehand.
#                 try:
#                     rank_id = int(rank_id)
#                 except ValueError:
#                     pass

#                 if rank_id == "all":
#                     bind_data["bind"]["everyone"] = True
#                 elif rank_id == 0:
#                     bind_data["bind"]["guest"] = True
#                 elif rank_id < 0:
#                     bind_data["bind"]["min"] = abs(rank_id)
#                 else:
#                     bind_data["bind"]["roleset"] = rank_id

#                 output.append(bind_data)

#         # group rank ranges
#         if data.get("ranges"):
#             for range_item in data["ranges"]:
#                 bind_data = {}

#                 bind_data["bind"] = {"type": bind_type, "id": int(bind_id)}
#                 bind_data["roles"] = range_item.get("roles")
#                 bind_data["nickname"] = range_item.get("nickname")
#                 bind_data["removeRoles"] = range_item.get("removeRoles")

#                 bind_data["bind"]["min"] = int(range_item.get("low"))
#                 bind_data["bind"]["max"] = int(range_item.get("high"))

#                 output.append(bind_data)

#     return output
