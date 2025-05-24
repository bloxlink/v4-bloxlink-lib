import pytest
from bloxlink_lib import GuildData, GuildSerializable
from bloxlink_lib.models.binds import BindCriteria, GuildBind, GroupBindData

pytestmark = pytest.mark.database


TEST_GROUP_ID = 1337


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

    @pytest.mark.asyncio_concurrent(group="migrators")
    async def test_migrate_null_values_with_value(
        self,
        test_guild: GuildSerializable,
    ):
        """Test the null value migrator with a value"""

        test_guild_data = GuildData(
            id=test_guild.id,
            welcomeMessage="Welcome to the server!",
        )

        assert test_guild_data.welcomeMessage == "Welcome to the server!"

    @pytest.mark.parametrize(
        "nickname_template",
        [
            ["roblox-name", "{roblox-name}"],
            ["roblox-id", "{roblox-id}"],
            ["{roblox-name}", "{roblox-name}"],
            ["roblox-id {roblox-name}", "{roblox-id} {roblox-name}"],
            ["[O1] group-rank", "[O1] {group-rank}"],
            ["{test} {roblox-name}", "{test} {roblox-name}"],
            [
                "{group-rank-6762663} | {roblox-name}",
                "{group-rank-6762663} | {roblox-name}",
            ],
            [
                "group-rank-6762663 | {roblox-name}",
                "{group-rank}-6762663 | {roblox-name}",
            ],
        ],
    )
    @pytest.mark.asyncio_concurrent(group="migrators")
    async def test_migrate_nickname_template(
        self,
        test_guild: GuildSerializable,
        nickname_template: list[str],
    ):
        """Test the nickname template migrator"""

        test_guild_data = GuildData(
            id=test_guild.id,
            nicknameTemplate=nickname_template[0],
        )

        assert test_guild_data.nicknameTemplate == nickname_template[1]

    @pytest.mark.asyncio_concurrent(group="migrators")
    async def test_migrate_binds(self, test_guild: GuildSerializable):
        """Test the binds migrator"""

        test_guild_data = GuildData(
            id=1,
            binds=[
                GuildBind(
                    criteria=BindCriteria(
                        type="group",
                        id=TEST_GROUP_ID,
                        group=GroupBindData(
                            dynamicRoles=True,
                        ),
                    ),
                    roles=["123"],
                ),
                GuildBind(
                    criteria=BindCriteria(
                        type="group",
                        id=TEST_GROUP_ID,
                        group=GroupBindData(
                            dynamicRoles=True,
                        ),
                    ),
                    roles=["567"],
                ),
                GuildBind(
                    criteria=BindCriteria(
                        type="group",
                        id=TEST_GROUP_ID,
                        group=GroupBindData(
                            everyone=True,
                        ),
                    ),
                    roles=["123"],
                ),
                GuildBind(
                    criteria=BindCriteria(
                        type="group",
                        id=TEST_GROUP_ID + 1,
                        group=GroupBindData(
                            everyone=True,
                        ),
                    ),
                    roles=[],
                ),
            ],
        )

        assert test_guild_data.binds == [
            GuildBind(
                criteria=BindCriteria(
                    type="group",
                    id=TEST_GROUP_ID,
                    group=GroupBindData(
                        dynamicRoles=True,
                    ),
                ),
                roles=["123", "567"],
            ),
            GuildBind(
                criteria=BindCriteria(
                    type="group",
                    id=TEST_GROUP_ID,
                    group=GroupBindData(
                        everyone=True,
                    ),
                ),
                roles=["123"],
            ),
            GuildBind(
                criteria=BindCriteria(
                    type="group",
                    id=TEST_GROUP_ID + 1,
                    group=GroupBindData(
                        everyone=True,
                    ),
                ),
                roles=[],
            ),
        ]
