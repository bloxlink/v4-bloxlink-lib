from pydantic import Field
from bloxlink_lib.models.base import BaseModel


class UserData(BaseModel):
    """Representation of a User's data in Bloxlink

    Attributes:
        id (int): The Discord ID of the user.
        robloxID (str): The roblox ID of the user's primary account.
        robloxAccounts (dict): All of the user's linked accounts, and any guild specific verifications.
    """

    id: int
    robloxID: str | None = None
    robloxAccounts: dict = Field(default_factory=lambda: {
                                 "accounts": [], "guilds": {}, "confirms": {}})
