from typing import Self, Type, Literal, Annotated
from pydantic import Field, field_validator
from bloxlink_lib.models.base import (
    PydanticList,
    BaseModel,
    PydanticDict,
    MemberSerializable,
)
from bloxlink_lib.models.base.serializable import GuildSerializable
from bloxlink_lib.models.schemas import BaseSchema, DatabaseDomains
from bloxlink_lib.validators import is_positive_number_as_str
from bloxlink_lib.models.binds import GuildBind
from bloxlink_lib.database.mongodb import (  # pylint: disable=no-name-in-module
    fetch_item,
    update_item,
)


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


MagicRoleTypes = Literal["Bloxlink Admin", "Bloxlink Updater", "Bloxlink Bypass"]

RestrictionTypes = Literal["users", "groups", "robloxAccounts", "roles"]

RestrictionSources = Literal[
    "ageLimit", "groupLock", "disallowAlts", "banEvader", "restrictions"
]


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


class GuildData(BaseSchema):
    """Representation of the stored settings for a guild"""

    id: Annotated[int, Field(alias="_id")]

    binds: Annotated[list[GuildBind], Field(default_factory=list)]

    verifiedRoleEnabled: bool = True
    verifiedRoleName: str | None = "Verified"  # deprecated
    verifiedRole: str = None

    unverifiedRoleEnabled: bool = True
    unverifiedRoleName: str | None = "Unverified"  # deprecated
    unverifiedRole: str = None

    verifiedDM: str | None = (
        ":wave: Welcome to **{server-name}**, {roblox-name}! Visit <{verify-url}> to change your account.\nFind more Roblox Communities at https://blox.link/communities !"
    )

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
    deleteCommands: Annotated[
        bool,
        Field(alias="ephemeralCommands", default=False),
    ]

    restrictions: PydanticList[GuildRestriction] = Field(default_factory=list)

    webhooks: Webhooks = None

    hasBot: bool = False
    proBot: bool = False

    nicknameTemplate: str = "{smart-name}"
    unverifiedNickname: str = ""

    magicRoles: PydanticDict[str, list[MagicRoleTypes]] = None

    premium: PydanticDict = Field(default_factory=PydanticDict)  # deprecated

    # Old bind fields.
    roleBinds: PydanticDict | None = None
    groupIDs: PydanticDict = None
    migratedBindsToV4: bool = False

    # field converters
    @field_validator("binds", mode="before")
    @classmethod
    def transform_binds(cls: Type[Self], binds: list) -> list[GuildBind]:
        """Transforms DB binds to GuildBinds"""

        if all(isinstance(b, GuildBind) for b in binds):
            return binds

        return [GuildBind(**b) for b in binds]

    @field_validator("deleteCommands", mode="before")
    @classmethod
    def transform_delete_commands(
        cls: Type[Self], delete_commands: int | None | bool
    ) -> bool:
        """Migrate the deleteCommands field."""

        from bloxlink_lib.models.migrators import (
            migrate_delete_commands,
        )

        return migrate_delete_commands(delete_commands)

    @field_validator("disallowBanEvaders", mode="before")
    @classmethod
    def transform_disallow_ban_evaders(
        cls: Type[Self], disallow_ban_evaders: bool | str | None
    ) -> bool:
        """Migrate the disallowBanEvaders field."""

        from bloxlink_lib.models.migrators import (
            migrate_disallow_ban_evaders,
        )

        return migrate_disallow_ban_evaders(disallow_ban_evaders)

    @field_validator("restrictions", mode="before")
    @classmethod
    def transform_restrictions(
        cls: Type[Self], restrictions: dict[str, dict[str, GuildRestriction]]
    ) -> list[GuildRestriction]:
        """Migrate the restrictions field."""

        from bloxlink_lib.models.migrators import migrate_restrictions

        return migrate_restrictions(restrictions)

    def model_post_init(self, __context):
        # merge verified roles into binds
        if self.verifiedRole:
            verified_role_bind = GuildBind(
                criteria={"type": "verified"}, roles=[self.verifiedRole]
            )

            if verified_role_bind not in self.binds:
                self.binds.append(verified_role_bind)

        if self.unverifiedRole:
            unverified_role_bind = GuildBind(
                criteria={"type": "unverified"}, roles=[self.unverifiedRole]
            )

            if unverified_role_bind not in self.binds:
                self.binds.append(unverified_role_bind)

        # # convert old binds
        # if self.roleBinds and not self.converted_binds:
        #     self.converted_binds = True

        #     for role_id, group_id in self.roleBinds.items():
        #         self.binds.append(binds_module.GuildBind(criteria={"type": "group", "group_id": group_id}, roles=[role_id]))

        #     self.roleBinds = None

    @staticmethod
    def database_domain() -> DatabaseDomains:
        """The database domain for the schema."""

        return DatabaseDomains.GUILDS


async def fetch_guild_data(
    guild: str | int | dict | GuildSerializable, *aspects
) -> GuildData:
    """
    Fetch a full guild from local cache, then redis, then database.
    Will populate caches for later access
    """

    if isinstance(guild, dict):
        guild_id = str(guild["id"])
    elif isinstance(guild, GuildSerializable):
        guild_id = str(guild.id)
    else:
        guild_id = str(guild)

    return await fetch_item("guilds", GuildData, guild_id, *aspects)


async def update_guild_data(
    guild: str | int | dict | GuildSerializable, **aspects
) -> None:
    """
    Update a guild's aspects in local cache, redis, and database.
    """

    if isinstance(guild, dict):
        guild_id = str(guild["id"])
    elif isinstance(guild, GuildSerializable):
        guild_id = str(guild.id)
    else:
        guild_id = str(guild)

    GuildData.model_validate({"id": guild_id, **aspects})

    return await update_item(GuildData, guild_id, **aspects)


# # RoleSerializable is not defined when the schema is first built, so we need to re-build it. TODO: make better
# GuildBind.model_rebuild()
