import pytest
from bloxlink_lib.models.roblox.binds import parse_template

from .utils.nickname_helpers import nickname_formatter, NicknameTestData

# fixtures
from .fixtures.users import test_discord_user_1
from .fixtures.roblox_users import test_roblox_user_1
from .fixtures.guilds import test_guild_1
from .fixtures.nicknames import (
    nickname_test_data,
    generic_template_test_data,
    NicknameTestCaseData,
)


class TestNicknames:
    """Tests related to bind nicknames."""

    @pytest.mark.asyncio_concurrent(group="nickname_tests")
    async def test_nicknames(
        self,
        test_roblox_user_1,
        test_discord_user_1,
        test_guild_1,
        nickname_test_data: NicknameTestCaseData,
    ):
        """Test that the nickname is correctly parsed with a valid Roblox user."""

        expected_nickname = nickname_test_data.expected_nickname
        nickname_template = nickname_test_data.nickname_fixture.nickname_template
        valid_roblox_user = nickname_test_data.nickname_fixture.valid_roblox_user
        valid_discord_user = nickname_test_data.nickname_fixture.valid_discord_user

        nickname = await parse_template(
            guild_id=test_guild_1.id,
            guild_name=test_guild_1.name,
            member=test_discord_user_1 if valid_discord_user else None,
            template=nickname_template,
            potential_binds=[],
            roblox_user=test_roblox_user_1 if valid_roblox_user else None,
            trim_nickname=True,
        )

        assert (
            nickname == nickname_test_data.expected_nickname
        ), f"Expected nickname to be {expected_nickname}, got {nickname}"

    @pytest.mark.asyncio_concurrent(group="nickname_generic_tests")
    async def test_generic_templates(
        self,
        test_guild_1,
        test_discord_user_1,
        generic_template_test_data: NicknameTestCaseData,
    ):
        """Test that the template is correctly parsed regardless if a Roblox account is linked."""

        expected_nickname = generic_template_test_data.expected_nickname
        nickname_template = (
            generic_template_test_data.nickname_fixture.nickname_template
        )
        valid_roblox_user = (
            generic_template_test_data.nickname_fixture.valid_roblox_user
        )
        valid_discord_user = (
            generic_template_test_data.nickname_fixture.valid_discord_user
        )

        nickname = await parse_template(
            guild_id=test_guild_1.id,
            guild_name=test_guild_1.name,
            member=test_discord_user_1 if valid_discord_user else None,
            template=nickname_template,
            potential_binds=[],
            roblox_user=test_roblox_user_1 if valid_roblox_user else None,
            trim_nickname=False,  # Parse the entire template
        )

        assert (
            nickname == generic_template_test_data.expected_nickname
        ), f"Expected nickname to be {expected_nickname}, got {nickname}"
