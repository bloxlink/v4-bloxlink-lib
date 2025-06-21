from typing import Callable
from unittest.mock import AsyncMock
import pytest
from bloxlink_lib import GuildData


@pytest.fixture()
def mock_guild_data(
    mocker,
) -> Callable[[GuildData], None]:
    """Mock the guild data"""

    def _mock_guild_data(guild_data: GuildData):
        mocker.patch(
            "bloxlink_lib.database.redis.redis.hmget",
            new_callable=AsyncMock,
            return_value={},
        )
        mocker.patch(
            "bloxlink_lib.database.redis.redis.hgetall",
            new_callable=AsyncMock,
            return_value={},
        )

        # Mock the fetch_item function that's used by fetch_guild_data
        mocker.patch(
            "bloxlink_lib.database.mongodb.fetch_item", return_value=guild_data
        )

    return _mock_guild_data
