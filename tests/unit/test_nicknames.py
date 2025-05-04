from typing import TYPE_CHECKING
import pytest
from bloxlink_lib.models.roblox.binds import parse_template

# fixtures
from .fixtures.users import test_military_member, MockUser
from .fixtures.guilds import military_guild
from .fixtures.nicknames import (
    nickname_test_data,
    generic_template_test_data,
    NicknameTestCaseData,
)

if TYPE_CHECKING:
    from bloxlink_lib import GuildSerializable, RobloxUser, MemberSerializable


class TestNicknames:
    """Tests related to bind nicknames."""

    @pytest.mark.asyncio_concurrent(group="nickname_tests")
    async def test_nicknames(
        self,
        military_guild: "GuildSerializable",
        test_military_member: MockUser,
        nickname_test_data: NicknameTestCaseData,
    ):
        """Test that the nickname is correctly parsed with a valid Roblox user."""

        expected_nickname = nickname_test_data.expected_nickname
        nickname_template = nickname_test_data.nickname_fixture.nickname_template
        include_roblox_user = nickname_test_data.nickname_fixture.include_roblox_user
        include_discord_user = nickname_test_data.nickname_fixture.include_discord_user

        nickname = await parse_template(
            guild_id=military_guild.id,
            guild_name=military_guild.name,
            member=test_military_member.discord_user if include_discord_user else None,
            template=nickname_template,
            potential_binds=[],
            roblox_user=(
                test_military_member.roblox_user if include_roblox_user else None
            ),
            trim_nickname=True,
        )

        assert (
            nickname == nickname_test_data.expected_nickname
        ), f"Expected nickname to be {expected_nickname}, got {nickname}"

    @pytest.mark.asyncio_concurrent(group="nickname_generic_tests")
    @pytest.mark.parametrize("include_roblox_user", [False, True])
    async def test_generic_templates(
        self,
        military_guild: "GuildSerializable",
        test_military_member: MockUser,
        include_roblox_user: bool,
        generic_template_test_data: NicknameTestCaseData,
    ):
        """Test that the template is correctly parsed regardless if a Roblox account is linked."""

        expected_nickname = generic_template_test_data.expected_nickname
        nickname_template = (
            generic_template_test_data.nickname_fixture.nickname_template
        )
        include_discord_user = (
            generic_template_test_data.nickname_fixture.include_discord_user
        )

        nickname = await parse_template(
            guild_id=military_guild.id,
            guild_name=military_guild.name,
            member=test_military_member.discord_user if include_discord_user else None,
            template=nickname_template,
            potential_binds=[],
            roblox_user=(
                test_military_member.roblox_user if include_roblox_user else None
            ),
            trim_nickname=False,  # Parse the entire template
        )

        assert (
            nickname == generic_template_test_data.expected_nickname
        ), f"Expected nickname to be {expected_nickname}, got {nickname}"
