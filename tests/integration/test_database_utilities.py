import pytest
from bloxlink_lib.models.schemas.guilds import (  # pylint: disable=no-name-in-module
    update_guild_data,
    fetch_guild_data,
    GuildData,
)
from bloxlink_lib.database.mongodb import _db_fetch, _db_update
from bloxlink_lib.models.migrators import *
from pydantic import ValidationError

pytestmark = pytest.mark.database


class TestIntegrationDatabaseUtilities:
    """Tests the database fetch and update utilities."""

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

    @pytest.mark.asyncio
    async def test_unset_guild_data_field(self, test_guild_id: int):
        await update_guild_data(test_guild_id, verifiedRoleName="Verified")
        assert (
            await fetch_guild_data(test_guild_id, "verifiedRoleName")
        ).verifiedRoleName == "Verified"

        await update_guild_data(test_guild_id, verifiedRoleName=None)

        guild_data = await _db_fetch(GuildData, test_guild_id, "verifiedRoleName")

        assert "verifiedRoleName" not in guild_data


class TestIntegrationDatabaseMigrators:
    """Tests the database migrators."""

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

        assert guild_data.verifiedRoleName is None
        assert guild_data.unverifiedRoleName is None

        assert guild_data.verifiedRole == "123"
        assert guild_data.unverifiedRole == "456"

    @pytest.mark.asyncio
    async def test_migrate_null_values(self, test_guild_id: int):
        await _db_update(
            GuildData,
            test_guild_id,
            set_aspects={"welcomeMessage": None},
            unset_aspects={},
        )

        guild_data = await fetch_guild_data(test_guild_id)

        assert guild_data.welcomeMessage is not None
