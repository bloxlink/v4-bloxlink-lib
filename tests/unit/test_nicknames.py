from typing import TYPE_CHECKING
import pytest
from pytest_mock import MockerFixture
from bloxlink_lib.models.roblox.binds import parse_template
from bloxlink_lib.models.binds import BindCriteria, GroupBindData
from bloxlink_lib.models.roblox.groups import RobloxGroup
from bloxlink_lib.test_utils.fixtures.users import MockUser
from tests.unit.utils.bind_helpers import nickname_formatter
from bloxlink_lib.test_utils.utils import mock_bind

# fixtures
from .fixtures import NicknameTestCaseData, NicknameTestData

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

    @pytest.mark.asyncio_concurrent(group="nickname_generic_tests")
    @pytest.mark.parametrize(
        "test_case",
        [
            NicknameTestData(
                nickname_template="{group-rank} {roblox-name}",
                expected_nickname="[L1] {roblox_user.username}",
                include_discord_user=True,
                include_roblox_user=False,
            ),
            NicknameTestData(
                nickname_template="{roblox-name}",
                expected_nickname="{roblox_user.username}",
                include_discord_user=True,
                include_roblox_user=False,
            ),
        ],
    )
    async def test_shorter_nicknames(
        self,
        test_guild: "GuildSerializable",
        test_group: RobloxGroup,
        test_group_member_bracketed_roleset: MockUser,
        test_case: NicknameTestData,
        mocker: MockerFixture,
    ):
        """Test that templates with brackets are parsed correctly if shorter nicknames are enabled."""

        expected_nickname = test_case.expected_nickname
        nickname_template = test_case.nickname_template

        expected_nickname = nickname_formatter(
            expected_nickname_format=expected_nickname,
            roblox_user=test_group_member_bracketed_roleset.roblox_user,
            discord_user=test_group_member_bracketed_roleset.discord_user,
            guild=test_guild,
        )

        group_bind = mock_bind(
            mocker,
            discord_roles=[],
            criteria=BindCriteria(
                type="group", id=test_group.id, group=GroupBindData(everyone=True)
            ),
            entity=test_group,
        )

        nickname = await parse_template(
            guild_id=test_guild.id,
            guild_name=test_guild.name,
            member=test_group_member_bracketed_roleset.discord_user,
            template=nickname_template,
            potential_binds=[group_bind],
            roblox_user=test_group_member_bracketed_roleset.roblox_user,
            trim_nickname=False,  # Parse the entire template
            shorter_nicknames=True,
        )

        assert (
            nickname == expected_nickname
        ), f"Expected nickname to be {expected_nickname}, got {nickname}"

    @pytest.mark.asyncio_concurrent(group="nickname_generic_tests")
    @pytest.mark.parametrize(
        "test_case",
        [
            NicknameTestData(
                nickname_template="{roblox-name}",
                expected_nickname="{roblox_user.username}",
                include_discord_user=True,
                include_roblox_user=False,
            ),
        ],
    )
    async def test_shorter_nicknames_disabled(
        self,
        test_guild: "GuildSerializable",
        test_group: RobloxGroup,
        test_group_member_bracketed_roleset: MockUser,
        test_case: NicknameTestData,
        mocker: MockerFixture,
    ):
        """Test that templates with brackets are parsed with full roleset names if shorter nicknames are disabled."""

        expected_nickname = test_case.expected_nickname
        nickname_template = test_case.nickname_template

        expected_nickname = nickname_formatter(
            expected_nickname_format=expected_nickname,
            roblox_user=test_group_member_bracketed_roleset.roblox_user,
            discord_user=test_group_member_bracketed_roleset.discord_user,
            guild=test_guild,
        )

        group_bind = mock_bind(
            mocker,
            discord_roles=[],
            criteria=BindCriteria(
                type="group", id=test_group.id, group=GroupBindData(everyone=True)
            ),
            entity=test_group,
        )

        nickname = await parse_template(
            guild_id=test_guild.id,
            guild_name=test_guild.name,
            member=test_group_member_bracketed_roleset.discord_user,
            template=nickname_template,
            potential_binds=[group_bind],
            roblox_user=test_group_member_bracketed_roleset.roblox_user,
            trim_nickname=False,  # Parse the entire template
            shorter_nicknames=True,
        )

        assert (
            nickname == expected_nickname
        ), f"Expected nickname to be {expected_nickname}, got {nickname}"
