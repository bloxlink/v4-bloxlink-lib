from typing import Annotated, Self, Type

from pydantic import Field, field_validator
from bloxlink_lib.models.base import BaseModel, PydanticDict, PydanticList
from bloxlink_lib.models.migrators import migrate_restrictions
from bloxlink_lib.models.schemas.guilds.guild_types import GroupLock, GuildRestriction, MagicRoleTypes, Webhooks
import bloxlink_lib.models.binds as binds_module


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
