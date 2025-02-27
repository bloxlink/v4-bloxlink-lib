from pydantic import Field
from bloxlink_lib.fetch import fetch_typed
from bloxlink_lib.models.base import BaseModel
from .base import get_entity
from .base_assets import RobloxBaseAsset


GAMEPASS_API = "https://economy.roblox.com/v1/game-pass"


class RobloxGamepassResponse(BaseModel):
    """Representation of the response from the Roblox Gamepass API."""

    id: int = Field(alias="TargetId")
    name: str = Field(alias="Name")
    description: str = Field(alias="Description")


class RobloxGamepass(RobloxBaseAsset):
    """Representation of a Gamepass on Roblox."""

    type: str = "gamepass"

    async def sync(self):
        """Load Gamepass data from Roblox"""

        if self.synced:
            return

        gamepass_data, _ = await fetch_typed(
            RobloxGamepassResponse, f"{GAMEPASS_API}/{self.id}/game-pass-product-info"
        )

        self.name = gamepass_data.name
        self.description = gamepass_data.description

        self.synced = True


async def get_gamepass(gamepass_id: int) -> RobloxGamepass:
    """Wrapper around get_entity() to get and sync a gamepass from Roblox.

    Args:
        gamepass_id (int): ID of the Gamepass.

    Returns:
        RobloxGamepass: A synced Roblox Gamepass.
    """

    return await get_entity("gamepass", gamepass_id)
