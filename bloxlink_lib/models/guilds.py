from typing import Mapping, Self, Type, Literal, Annotated
from pydantic import Field, field_validator
import hikari
from .base import PydanticList,  BaseModel, PydanticDict, MemberSerializable
from ..validators import is_positive_number_as_str
from .migrators import migrate_restrictions
import bloxlink_lib.models.binds as binds_module


class UserInfoFieldMapping(BaseModel):
    """Map a field from Bloxlink-expected to developer-expected"""

    robloxID: str = "robloxID"
    guildID: str = "guildID"
    discordID: str = "discordID"
    robloxUsername: str = "robloxUsername"
    discordUsername: str = "discordUsername"


class UserInfoWebhook(BaseModel):
    """Webhook settings for the userInfo webhook"""

    url: str
    fieldMapping: UserInfoFieldMapping = None


class Webhooks(BaseModel):
    """Fired when certain actions happen on Bloxlink"""

    authentication: str
    userInfo: UserInfoWebhook = None


class GroupLock(BaseModel):
    """Group lock settings for a group"""

    groupName: str = None
    dmMessage: str | None = None
    roleSets: Annotated[list[int], Field(default_factory=list)]
    verifiedAction: Literal["kick", "dm"] = "kick"
    unverifiedAction: Literal["kick", "dm"] = "kick"


MagicRoleTypes = Literal["Bloxlink Admin",
                         "Bloxlink Updater", "Bloxlink Bypass"]

RestrictionTypes = Literal[
    "users",
    "groups",
    "robloxAccounts",
    "roles"
]

RestrictionSources = Literal["ageLimit", "groupLock",
                             "disallowAlts", "banEvader", "restrictions"]


class GuildRestriction(BaseModel):
    """Server restrictions set by the server owner"""

    id: int
    displayName: Annotated[str, Field(alias="name")]
    addedBy: Annotated[str, is_positive_number_as_str]
    reason: str | None = None
    type: RestrictionTypes

    def __str__(self) -> str:
        return f"{self.displayName or ''} ({self.id})\n> Reason: {self.reason or "N/A"}\n> Added by: {MemberSerializable.user_mention(self.addedBy)}"

    def __eq__(self, other):
        return self.id == other.id and self.type == other.type


class GuildData(BaseModel):
    """Representation of the stored settings for a guild"""

    id: int
    binds: Annotated[list[binds_module.GuildBind], Field(default_factory=list)]

    @field_validator("binds", mode="before")
    @classmethod
    def transform_binds(cls: Type[Self], binds: list) -> list[binds_module.GuildBind]:
        if all(isinstance(b, binds_module.GuildBind) for b in binds):
            return binds

        return [binds_module.GuildBind(**b) for b in binds]

    verifiedRoleEnabled: bool = True
    verifiedRoleName: str | None = "Verified"  # deprecated
    verifiedRole: str = None

    unverifiedRoleEnabled: bool = True
    unverifiedRoleName: str | None = "Unverified"  # deprecated
    unverifiedRole: str = None

    verifiedDM: str = ":wave: Welcome to **{server-name}**, {roblox-name}! Visit <{verify-url}> to change your account.\nFind more Roblox Communities at https://blox.link/communities !"

    ageLimit: int = None
    autoRoles: bool = True
    autoVerification: bool = True
    disallowAlts: bool | None = False
    disallowBanEvaders: bool | None = False
    banRelatedAccounts: bool | None = False
    unbanRelatedAccounts: bool | None = False
    dynamicRoles: bool | None = True
    groupLock: PydanticDict[str, GroupLock] = None
    highTrafficServer: bool = False
    allowOldRoles: bool = False

    restrictions: PydanticList[GuildRestriction] = Field(default_factory=list)

    @field_validator("restrictions", mode="before")
    @classmethod
    def transform_restrictions(cls: Type[Self], restrictions: dict[str, dict[str, GuildRestriction]]) -> list[GuildRestriction]:
        return migrate_restrictions(restrictions)

    webhooks: Webhooks = None

    hasBot: bool = False
    proBot: bool = False

    nicknameTemplate: str = "{smart-name}"
    unverifiedNickname: str = ""

    magicRoles: PydanticDict[str, list[MagicRoleTypes]] = None

    premium: PydanticDict = Field(
        default_factory=PydanticDict)  # deprecated

    # Old bind fields.
    roleBinds: PydanticDict = None
    groupIDs: PydanticDict = None
    migratedBindsToV4: bool = False

    def model_post_init(self, __context):
        # merge verified roles into binds
        if self.verifiedRole:
            verified_role_bind = binds_module.GuildBind(
                criteria={"type": "verified"}, roles=[self.verifiedRole])

            if verified_role_bind not in self.binds:
                self.binds.append(verified_role_bind)

        if self.unverifiedRole:
            unverified_role_bind = binds_module.GuildBind(
                criteria={"type": "unverified"}, roles=[self.unverifiedRole])

            if unverified_role_bind not in self.binds:
                self.binds.append(unverified_role_bind)

        # # convert old binds
        # if self.roleBinds and not self.converted_binds:
        #     self.converted_binds = True

        #     for role_id, group_id in self.roleBinds.items():
        #         self.binds.append(binds_module.GuildBind(criteria={"type": "group", "group_id": group_id}, roles=[role_id]))

        #     self.roleBinds = None


# RoleSerializable is not defined when the schema is first built, so we need to re-build it. TODO: make better
binds_module.GuildBind.model_rebuild()
