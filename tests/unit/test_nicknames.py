import pytest
from bloxlink_lib.models.roblox.binds import parse_template

from .utils.nickname_helpers import nickname_formatter

# fixtures
from .fixtures.users import test_discord_user_1
from .fixtures.roblox_users import test_roblox_user_1
from .fixtures.guilds import test_guild_1


class TestNicknames:
    """Tests related to bind nicknames."""

    @pytest.mark.parametrize(
        "test_nickname_template,expected_nickname",
        [
            # roblox nickname templates
            ("{roblox-name}", "{roblox_user.username}"),
            ("{roblox-id}", "{roblox_user.id}"),
            ("{display-name}", "{roblox_user.display_name}"),
            ("{smart-name}", "{roblox_user.display_name} (@{roblox_user.username})"),
            ("{roblox-age}", "{roblox_user.age_days}"),
            ("{disable-nicknaming}", None),
            ("{group-rank}", "Guest"),
            # discord nickname templates
            ("{discord-name}", "{discord_user.username}"),
            ("{discord-nick}", "{discord_user.nickname}"),
            ("{discord-global-name}", "{discord_user.global_name}"),
            ("{discord-id}", "{discord_user.id}"),
            # combined
            (
                "[{group-rank}] {roblox-name}",
                "[Guest] {roblox_user.username}",
            ),
            (
                "[{group-rank}] {roblox-name} {roblox-id}",
                "[Guest] {roblox_user.username} {roblox_user.id}",
            ),
        ],
    )
    async def test_nicknames_valid_roblox_user_not_in_group(
        self,
        test_roblox_user_1,
        test_nickname_template,
        expected_nickname,
        test_discord_user_1,
        test_guild_1,
    ):
        """Test that the nickname is correctly parsed with a valid Roblox user."""

        expected_nickname = nickname_formatter(
            expected_nickname_format=expected_nickname,
            roblox_user=test_roblox_user_1,
            discord_user=test_discord_user_1,
        )

        nickname = await parse_template(
            guild_id=test_guild_1.id,
            guild_name=test_guild_1.name,
            member=test_discord_user_1,
            template=test_nickname_template,
            potential_binds=[],
            roblox_user=test_roblox_user_1,
            trim_nickname=True,
        )

        assert nickname == expected_nickname

    @pytest.mark.parametrize(
        "test_nickname_template,expected_nickname",
        [
            # roblox nickname templates
            ("{roblox-name}", "{roblox_user.username}"),
            ("{roblox-id}", "{roblox_user.id}"),
            ("{display-name}", "{roblox_user.display_name}"),
            (
                "{smart-name}",
                "{roblox_user.display_name} (@{roblox_user.username})",
            ),
            # TODO: find a way to fix this
            # ("{roblox-age}", lfc(
            #     "{}".format,
            #     (datetime.datetime.now().replace(
            #         tzinfo=None) - test_roblox_user_1.created).days
            # )),
            ("{disable-nicknaming}", None),
            ("{group-rank}", "Guest"),
            # discord nickname templates
            ("{discord-name}", "{discord_user.username}"),
            ("{discord-nick}", "{discord_user.nickname}"),
            ("{discord-global-name}", "{discord_user.global_name}"),
            ("{discord-id}", "{discord_user.id}"),
            # combined
            (
                "[{group-rank}] {roblox-name}",
                "[Guest] {roblox_user.username}",
            ),
            (
                "[{group-rank}] {roblox-name} {roblox-id}",
                "[Guest] {roblox_user.username} {roblox_user.id}",
            ),
        ],
    )
    async def test_nicknames_valid_roblox_user_in_group(
        self,
        test_nickname_template,
        expected_nickname,
        test_discord_user_1,
        test_roblox_user_1,
        test_guild_1,
    ):
        """Test that the nickname is correctly parsed with a valid Roblox user."""

        expected_nickname = nickname_formatter(
            expected_nickname_format=expected_nickname,
            roblox_user=test_roblox_user_1,
            discord_user=test_discord_user_1,
        )

        nickname = await parse_template(
            guild_id=test_guild_1.id,
            guild_name=test_guild_1.name,
            member=test_discord_user_1,
            template=test_nickname_template,
            potential_binds=[],
            roblox_user=test_roblox_user_1,
            trim_nickname=True,
        )

        assert nickname == expected_nickname
