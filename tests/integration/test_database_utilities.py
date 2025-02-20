import pytest
from bloxlink_lib.database import mongodb
from pydantic import ValidationError


class TestUpdatingGuildData:
    """Tests for converting V3 whole group binds to V4."""

    @pytest.mark.parametrize("test_input", ["sadasda", "Very awesome role"])
    async def test_update_guild_data(
        self, test_input, start_docker_services, wait_for_redis
    ):
        await mongodb.update_guild_data(1, verifiedRoleName=test_input)

        assert (
            await mongodb.fetch_guild_data(1, "verifiedRoleName")
        ).verifiedRoleName == test_input

    @pytest.mark.parametrize("test_input", [5, 0, -1])
    async def test_update_guild_data_invalid_input_fails(
        self, test_input, start_docker_services, wait_for_redis
    ):
        with pytest.raises(ValidationError) as e:
            await mongodb.update_guild_data(1, verifiedRoleName=test_input)

        assert issubclass(e.type, ValidationError)
