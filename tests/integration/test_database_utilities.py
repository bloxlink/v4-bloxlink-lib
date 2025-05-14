import pytest
from bloxlink_lib.models.schemas.guilds import (  # pylint: disable=no-name-in-module
    update_guild_data,
    fetch_guild_data,
)
from bloxlink_lib.models.migrators import *
from pydantic import ValidationError


class TestIntegrationDatabaseUtilities:
    """Tests the database fetch and update utilities."""

    pytestmark = pytest.mark.database_utilities

    @pytest.mark.parametrize("test_input", ["sadasda", "Very awesome role"])
    @pytest.mark.asyncio
    async def test_update_guild_data(self, test_input: str, test_guild_id: int):
        await update_guild_data(test_guild_id, verifiedRoleName=test_input)

        assert (
            await fetch_guild_data(test_guild_id, "verifiedRoleName")
        ).verifiedRoleName == test_input

    @pytest.mark.parametrize("test_input", [5, 0, -1])
    @pytest.mark.asyncio
    async def test_update_guild_data_invalid_input_fails(
        self, test_input: int, test_guild_id: int
    ):
        with pytest.raises(ValidationError) as e:
            await update_guild_data(test_guild_id, verifiedRoleName=test_input)

        assert issubclass(e.type, ValidationError)


class TestIntegrationDatabaseMigrators:
    """Tests the database migrators."""

    pytestmark = pytest.mark.migrators

    @pytest.mark.asyncio
    async def test_migrate_verified_role_name(self, test_guild_id: int):
        await update_guild_data(
            test_guild_id,
            verifiedRoleName="Verified",
            unverifiedRoleName="Unverified",
            verifiedRole="123",
            unverifiedRole="456",
        )

        guild_data = await fetch_guild_data(test_guild_id)

        assert getattr(guild_data, "verifiedRoleName", None) is None
        assert getattr(guild_data, "unverifiedRoleName", None) is None

        assert getattr(guild_data, "verifiedRole", None) == "123"
        assert getattr(guild_data, "unverifiedRole", None) == "456"
