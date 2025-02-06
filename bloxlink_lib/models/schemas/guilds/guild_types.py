from typing import Mapping, Self, Type, Literal, Annotated
from pydantic import Field, field_validator
from bloxlink_lib.models.base import BaseModel
from bloxlink_lib.models.base.serializable import MemberSerializable
from bloxlink_lib.validators import is_positive_number_as_str


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


class GuildRestriction(BaseModel):
    """Server restrictions set by the server owner"""

    id: int
    displayName: Annotated[str, Field(alias="name")]
    addedBy: Annotated[str, is_positive_number_as_str]
    reason: str | None = None
    type: RestrictionTypes

    def __str__(self) -> str:
        return f"{self.displayName or ''} ({self.id})\n> Reason: {self.reason or "N/A"}\n> Added by: {MemberSerializable.user_mention(self.addedBy)}>"

    def __eq__(self, other):
        return self.id == other.id and self.type == other.type
