import pytest
from bloxlink_lib import GuildData, GuildSerializable

pytestmark = pytest.mark.database


class TestVerifiedRoleMigrators:
    """Test the logic of verified/unverified role migrators"""

    @pytest.mark.asyncio_concurrent(group="migrators")
    async def test_migrate_verified_role_name(
        self,
        test_guild: GuildSerializable,
    ):
        """Test the verified role name migrator"""

        test_guild_data = GuildData(
            id=test_guild.id,
            verifiedRoleName="Verified",
            verifiedRole="123",
        )

        assert test_guild_data.verifiedRoleName is None
        assert test_guild_data.verifiedRole == "123"

    @pytest.mark.asyncio_concurrent(group="migrators")
    async def test_migrate_unverified_role_name(
        self,
        test_guild: GuildSerializable,
    ):
        """Test the unverified role name migrator"""

        test_guild_data = GuildData(
            id=test_guild.id,
            unverifiedRoleName="Unverified",
            unverifiedRole="456",
        )

        assert test_guild_data.unverifiedRoleName is None
        assert test_guild_data.unverifiedRole == "456"

    @pytest.mark.asyncio_concurrent(group="migrators")
    async def test_migrate_verified_with_unverified_role_names(
        self,
        test_guild: GuildSerializable,
    ):
        """Test the verified role name and unverified role name migrator"""

        test_guild_data = GuildData(
            id=test_guild.id,
            unverifiedRoleName="Unverified",
            unverifiedRole="456",
            verifiedRoleName="Verified",
            verifiedRole="123",
        )

        assert test_guild_data.unverifiedRoleName is None
        assert test_guild_data.unverifiedRole == "456"

        assert test_guild_data.verifiedRoleName is None
        assert test_guild_data.verifiedRole == "123"

    @pytest.mark.asyncio_concurrent(group="migrators")
    async def test_default_verified_role_name(
        self,
        test_guild: GuildSerializable,
    ):
        """Test the default verified role settings"""

        test_guild_data = GuildData(id=test_guild.id)

        assert test_guild_data.unverifiedRoleName is "Unverified"
        assert test_guild_data.unverifiedRole is None

        assert test_guild_data.verifiedRoleName is "Verified"
        assert test_guild_data.verifiedRole is None

    @pytest.mark.asyncio_concurrent(group="migrators")
    async def test_migrate_null_values(
        self,
        test_guild: GuildSerializable,
    ):
        """Test the null value migrator"""

        test_guild_data = GuildData(
            id=test_guild.id,
            welcomeMessage=None,
        )

        assert test_guild_data.welcomeMessage is not None
