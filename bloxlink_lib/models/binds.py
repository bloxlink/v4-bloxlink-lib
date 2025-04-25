from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    NotRequired,
    TypedDict,
    Annotated,
    Self,
    Type,
)

from pydantic import Field, ValidationError

from bloxlink_lib.models.base import (
    BaseModel,
    CoerciveSet,
    SnowflakeSet,
    RoleSerializable,
    MemberSerializable,
)
from bloxlink_lib.models.roblox import RobloxEntity, create_entity
from bloxlink_lib.utils import find

if TYPE_CHECKING:
    from hikari import Member

    from .roblox.base_assets import RobloxBaseAsset
    from .roblox.groups import RobloxGroup
    from .schemas import GuildData
    from .roblox.users import MemberSerializable, RobloxUser


VALID_BIND_TYPES = Literal[
    "group", "asset", "badge", "gamepass", "verified", "unverified"
]
BIND_GROUP_SUBTYPES = Literal["role_bind", "full_group"]


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
    everyone: bool | None = False
    guest: bool | None = False
    min: int | None = None
    max: int | None = None
    roleset: int | None = None
    ####################

    dynamicRoles: bool = False  # full group bind

    def model_post_init(self, __context: Any) -> None:
        if (self.min or self.max) and not all([self.min, self.max]):
            raise ValidationError("Both min and max range must be set.")

        if self.roleset and (self.min or self.max):
            raise ValidationError("Either a Roleset or range can be set.")

        if self.everyone and (self.guest or self.min or self.max or self.roleset):
            raise ValidationError(
                "Everyone condition cannot have any other conditions."
            )


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
    roles: Annotated[list[str], Field(default_factory=list)]
    remove_roles: Annotated[list[str], Field(default_factory=list, alias="removeRoles")]

    criteria: BindCriteria
    data: BindData | None = Field(default=None)

    # Excluded fields. These are used for the bind algorithms.
    pending_new_roles: Annotated[list[str], Field(exclude=True, default_factory=list)]
    entity: RobloxEntity | None = Field(exclude=True, default=None)
    type: VALID_BIND_TYPES | None = Field(exclude=True, default=None)
    subtype: BIND_GROUP_SUBTYPES | None = Field(exclude=True, default=None)
    highest_role: RoleSerializable | None = Field(
        exclude=True, default=None
    )  # highest role in the guild

    def model_post_init(self, __context):
        self.entity = self.entity or create_entity(self.criteria.type, self.criteria.id)
        self.type = self.criteria.type

        if self.type == "group":
            self.subtype = (
                "full_group" if self.criteria.group.dynamicRoles else "role_bind"
            )

    @classmethod
    def from_V3(cls: Type[Self], guild_data: GuildData | dict):
        """Convert V3 binds to V4 binds."""

        whole_group_binds = getattr(
            guild_data, "groupIDs", guild_data.get("groupIDs", {})
        )
        role_binds = getattr(guild_data, "roleBinds", guild_data.get("roleBinds", {}))

        converted_binds: list[Self] = []

        for group_id, group_data in whole_group_binds.items():
            new_bind = cls(
                nickname=group_data.get("nickname") or None,
                criteria=BindCriteria(
                    type="group", id=int(group_id), group={"dynamicRoles": True}
                ),
                remove_roles=group_data.get("removeRoles") or [],
                subtype="full_group",
                data=BindData(displayName=group_data.get("groupName")),
            )

            converted_binds.append(new_bind)

        for bind_type, binds in role_binds.items():
            match bind_type:
                case "groups":
                    for group_id, group_bind_data in binds.items():
                        for rank_id, criteria_data in group_bind_data.get(
                            "binds", {}
                        ).items():
                            new_bind = cls(
                                nickname=criteria_data.get("nickname") or None,
                                criteria=BindCriteria(
                                    type="group",
                                    id=int(group_id),
                                    group=GroupBindData(
                                        everyone=rank_id == "all",
                                        guest=rank_id == "0",
                                        roleset=(
                                            int(rank_id)
                                            if rank_id not in ("all", "0")
                                            else None
                                        ),
                                    ),
                                ),
                                remove_roles=criteria_data.get("removeRoles") or [],
                                roles=criteria_data.get("roles") or [],
                                data=BindData(
                                    displayName=group_bind_data.get("groupName")
                                ),
                            )

                            converted_binds.append(new_bind)

                        for criteria_data in group_bind_data.get("ranges", []):
                            new_bind = cls(
                                nickname=group_bind_data.get("nickname") or None,
                                criteria=BindCriteria(
                                    type="group",
                                    id=int(group_id),
                                    group={
                                        "min": criteria_data.get("low"),
                                        "max": criteria_data.get("high"),
                                    },
                                ),
                                remove_roles=group_bind_data.get("removeRoles") or [],
                                data=BindData(
                                    displayName=group_bind_data.get("groupName")
                                ),
                            )

                            converted_binds.append(new_bind)

                case "assets" | "badges" | "gamePasses":
                    for entity_id, bind_data in binds.items():
                        if bind_type == "gamePasses":
                            bind_type = "gamepass"
                        else:
                            bind_type = bind_type[:-1]

                        new_bind = cls(
                            nickname=bind_data.get("nickname") or None,
                            roles=bind_data.get("roles") or [],
                            remove_roles=bind_data.get("removeRoles") or [],
                            criteria=BindCriteria(type=bind_type, id=int(entity_id)),
                            data=BindData(displayName=bind_data.get("displayName")),
                        )

                        converted_binds.append(new_bind)

        return converted_binds

    def calculate_highest_role(self, guild_roles: dict[str, RoleSerializable]) -> None:
        """Calculate the highest role in the guild for this bind."""

        if self.roles and not self.highest_role:
            filtered_binds = filter(
                lambda r: str(r.id) in self.roles and self.nickname,
                guild_roles.values(),
            )

            if list(filtered_binds):
                self.highest_role = max(filtered_binds, key=lambda r: r.position)

    async def satisfies_for(
        self,
        guild_roles: dict[int, RoleSerializable],
        member: Member | MemberSerializable,
        roblox_user: RobloxUser | None = None,
    ) -> tuple[bool, SnowflakeSet, CoerciveSet[str], SnowflakeSet]:
        """Check if a user satisfies the requirements for this bind."""

        ineligible_roles = SnowflakeSet()
        additional_roles = SnowflakeSet()
        missing_roles = CoerciveSet[str]()

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

                await group.sync_for(roblox_user, sync=True)

                user_roleset = group.user_roleset

                # check if the user has any group roleset roles they shouldn't have
                if self.criteria.group.dynamicRoles:
                    for roleset in group.rolesets.values():
                        for role_id in member.role_ids:
                            if (
                                role_id in guild_roles
                                and guild_roles[role_id].name == roleset.name
                                and str(roleset) != str(user_roleset)
                            ):
                                ineligible_roles.add(role_id)

                if self.criteria.id in roblox_user.groups:
                    # full group bind. check for a matching roleset
                    if self.criteria.group.dynamicRoles:
                        roleset_role = find(
                            lambda r: r.name == user_roleset.name, guild_roles.values()
                        )

                        if roleset_role:
                            additional_roles.add(roleset_role.id)
                            return (
                                True,
                                additional_roles,
                                missing_roles,
                                ineligible_roles,
                            )

                        missing_roles.add(user_roleset.name)

                    if self.criteria.group.everyone:
                        return True, additional_roles, missing_roles, ineligible_roles

                    if self.criteria.group.guest:
                        return False, additional_roles, missing_roles, ineligible_roles

                    if (self.criteria.group.min and self.criteria.group.max) and (
                        self.criteria.group.min
                        <= group.user_roleset.rank
                        <= self.criteria.group.max
                    ):
                        return True, additional_roles, missing_roles, ineligible_roles

                    if self.criteria.group.roleset:
                        roleset = self.criteria.group.roleset
                        return (
                            group.user_roleset.rank == roleset
                            or (
                                roleset < 0 and group.user_roleset.rank >= abs(roleset)
                            ),
                            additional_roles,
                            missing_roles,
                            ineligible_roles,
                        )

                    return False, additional_roles, missing_roles, ineligible_roles

                # Not in the group.
                # Return whether the bind is for guests only
                return (
                    self.criteria.group.guest,
                    additional_roles,
                    missing_roles,
                    ineligible_roles,
                )

            case "badge" | "gamepass" | "asset":
                asset: RobloxBaseAsset = self.entity

                return (
                    await roblox_user.owns_asset(asset),
                    additional_roles,
                    missing_roles,
                    ineligible_roles,
                )

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
                    content = f"{group.roleset_name_string(self.criteria.group.min, bold_name=False)} to {
                        group.roleset_name_string(self.criteria.group.max, bold_name=False)}"

                elif self.criteria.group.roleset:
                    content = group.roleset_name_string(
                        abs(self.criteria.group.roleset), bold_name=False
                    )

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

        return f"{self.description_prefix}{' ' if content else ''}{f'**{content}**' if content else ''}"

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
            # extended_description is not used in case we want the description to be shorter
            return "- _All users in **this** group receive the role matching their group rank name_"

        role_mentions = ", ".join(f"<@&{val}>" for val in self.roles)
        remove_role_mentions = ", ".join(f"<@&{val}>" for val in self.remove_roles)
        new_roles_list = ", ".join(f"{val} [NEW]" for val in self.pending_new_roles)

        return (
            f"- _{extended_description} receive the "
            f"role{'s' if len(self.roles) > 1 or len(self.pending_new_roles) > 1 else ''} {
                role_mentions}{new_roles_list}"
            f"{'' if len(self.remove_roles) == 0 else f', and have these roles removed: {
                remove_role_mentions}'}_"
        )

    def __eq__(self, other: GuildBind) -> bool:
        """
        Check if two GuildBind objects are equal.
        We define this ourselves since there are other fields that are not included in the comparison.
        """

        return (
            isinstance(other, GuildBind)
            and self.criteria == getattr(other, "criteria", None)
            and self.roles == getattr(other, "roles", None)
            and self.remove_roles == getattr(other, "remove_roles", None)
            and self.nickname == getattr(other, "nickname", None)
        )

    def __hash__(self) -> int:
        return hash(
            (self.criteria, tuple(self.roles), tuple(self.remove_roles), self.nickname)
        )


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

    from bloxlink_lib.models.roblox.binds import get_binds

    guild_binds = await get_binds(guild_id, category=bind_type, bind_id=bind_id)

    # sync the first 5 binds
    for bind in guild_binds[:5]:
        await bind.entity.sync()

    bind_strings = [str(bind) for bind in guild_binds[:5]]
    output = "\n".join(bind_strings)

    if len(guild_binds) > 5:
        output += (
            f"\n_... and {len(guild_binds) - 5} more. "
            f"Click [here](https://www.blox.link/dashboard/guilds/{
                guild_id}/binds) to view the rest!_"
        )
    return output
