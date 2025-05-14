import pytest
from bloxlink_lib.models.roblox.binds import get_binds


class TestIntegrationBinds:
    """Tests for converting V3 whole group binds to V4."""

    @pytest.mark.asyncio
    async def test_get_binds(self, test_guild_id: int):
        await get_binds(test_guild_id, "group")
