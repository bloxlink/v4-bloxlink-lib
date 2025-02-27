import pytest
from bloxlink_lib.models.schemas.guilds import (  # pylint: disable=no-name-in-module
    update_guild_data,
    fetch_guild_data,
)
from pydantic import ValidationError


class TestUpdatingGuildData:
    """Tests for converting V3 whole group binds to V4."""

    @pytest.mark.parametrize("test_input", ["sadasda", "Very awesome role"])
    async def test_update_guild_data(
        self, test_input, start_docker_services, wait_for_redis
    ):
        await update_guild_data(1, verifiedRoleName=test_input)

        assert (
            await fetch_guild_data(1, "verifiedRoleName")
        ).verifiedRoleName == test_input

    @pytest.mark.parametrize("test_input", [5, 0, -1])
    async def test_update_guild_data_invalid_input_fails(
        self, test_input, start_docker_services, wait_for_redis
    ):
        with pytest.raises(ValidationError) as e:
            await update_guild_data(1, verifiedRoleName=test_input)

        assert issubclass(e.type, ValidationError)
