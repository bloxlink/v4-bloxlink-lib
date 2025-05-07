from typing import TYPE_CHECKING
import pytest
from bloxlink_lib.models.roblox.binds import parse_template

# fixtures
from .fixtures import NicknameTestCaseData, MockUser

if TYPE_CHECKING:
    from bloxlink_lib import GuildSerializable, RobloxUser, MemberSerializable


pytestmark = pytest.mark.nicknames


class TestNicknames:
    """Tests related to bind nicknames."""

    @pytest.mark.asyncio_concurrent(group="nickname_tests")
    async def test_nicknames(
        self,
        test_guild: "GuildSerializable",
        test_group_member: MockUser,
        nickname_test_data: NicknameTestCaseData,
    ):
        """Test that the nickname is correctly parsed with a valid Roblox user."""

        expected_nickname = nickname_test_data.expected_nickname
        nickname_template = nickname_test_data.nickname_fixture.nickname_template
        include_roblox_user = nickname_test_data.nickname_fixture.include_roblox_user
        include_discord_user = nickname_test_data.nickname_fixture.include_discord_user

        nickname = await parse_template(
            guild_id=test_guild.id,
            guild_name=test_guild.name,
            member=test_group_member.discord_user if include_discord_user else None,
            template=nickname_template,
            potential_binds=[],
            roblox_user=(
                test_group_member.roblox_user if include_roblox_user else None
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
        test_guild: "GuildSerializable",
        test_group_member: MockUser,
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
            guild_id=test_guild.id,
            guild_name=test_guild.name,
            member=test_group_member.discord_user if include_discord_user else None,
            template=nickname_template,
            potential_binds=[],
            roblox_user=(
                test_group_member.roblox_user if include_roblox_user else None
            ),
            trim_nickname=False,  # Parse the entire template
        )

        assert (
            nickname == generic_template_test_data.expected_nickname
        ), f"Expected nickname to be {expected_nickname}, got {nickname}"
