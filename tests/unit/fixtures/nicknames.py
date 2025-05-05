from collections import namedtuple
import pytest
from bloxlink_lib import BaseModel, GuildSerializable
from tests.unit.utils import nickname_formatter
from . import MockUser

__all__ = [
    "NicknameTestCaseData",
    "NicknameTestData",
    "nickname_test_data",
    "generic_template_test_data",
]

NicknameTestCaseData = namedtuple(
    "NicknameTestCaseData", ["nickname_fixture", "expected_nickname"]
)


class NicknameTestData(BaseModel):
    """Represents a scenario for a user's nickname"""

    nickname_template: str
    expected_nickname: str | None
    include_roblox_user: bool = None
    include_discord_user: bool = None


@pytest.fixture(
    scope="function",
    params=[
        NicknameTestData(
            nickname_template="{roblox-name}",
            expected_nickname="{roblox_user.username}",
            include_roblox_user=True,
            include_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{roblox-id}",
            expected_nickname="{roblox_user.id}",
            include_roblox_user=True,
            include_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{display-name}",
            expected_nickname="{roblox_user.display_name}",
            include_roblox_user=True,
            include_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{smart-name}",
            expected_nickname="{roblox_user.display_name} (@{roblox_user.username})",
            include_roblox_user=True,
            include_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{roblox-age}",
            expected_nickname="{roblox_user.age_days}",
            include_roblox_user=True,
            include_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{disable-nicknaming}",
            expected_nickname=None,
            include_roblox_user=True,
            include_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{group-rank}",
            expected_nickname="Guest",
            include_roblox_user=True,
            include_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="[{group-rank}] {roblox-name}",
            expected_nickname="[Guest] {roblox_user.username}",
            include_roblox_user=True,
            include_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="[{group-rank}] {roblox-name} {roblox-id}",
            expected_nickname="[Guest] {roblox_user.username} {roblox_user.id}",
            include_roblox_user=True,
            include_discord_user=True,
        ),
    ],
)
def nickname_test_data(
    request,
    test_group_member: MockUser,
) -> NicknameTestCaseData:
    expected_nickname = request.param.expected_nickname
    include_roblox_user = request.param.include_roblox_user
    include_discord_user = request.param.include_discord_user

    expected_nickname = nickname_formatter(
        expected_nickname_format=expected_nickname,
        roblox_user=(test_group_member.roblox_user if include_roblox_user else None),
        discord_user=(test_group_member.discord_user if include_discord_user else None),
    )

    return NicknameTestCaseData(
        nickname_fixture=request.param, expected_nickname=expected_nickname
    )


@pytest.fixture(
    scope="function",
    params=[
        # Tests not dependent on a Roblox user being linked to a Discord user
        NicknameTestData(
            nickname_template="{prefix}",
            expected_nickname="/",
            include_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{server-name}",
            expected_nickname="{guild.name}",
            include_discord_user=True,
        ),
        # NicknameTestData(
        #     nickname_template="{discord-mention}",
        #     expected_nickname="{discord_user.mention}",
        #     include_discord_user=True,
        # ),
        NicknameTestData(
            nickname_template="{discord-name}",
            expected_nickname="{discord_user.username}",
            include_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{discord-nick}",
            expected_nickname="{discord_user.nickname}",
            include_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{discord-global-name}",
            expected_nickname="{discord_user.global_name}",
            include_discord_user=True,
        ),
        # NicknameTestData(
        #     nickname_template="{discord-id}",
        #     expected_nickname="{discord_user.id}",
        #     include_discord_user=True,
        # ),
        NicknameTestData(
            nickname_template="{verify-url}",
            expected_nickname="https://blox.link/verify",
            include_discord_user=True,
        ),
    ],
)
def generic_template_test_data(
    request,
    test_group_member: MockUser,
    test_guild: "GuildSerializable",
) -> NicknameTestCaseData:
    expected_nickname = request.param.expected_nickname
    include_roblox_user = request.param.include_roblox_user
    include_discord_user = request.param.include_discord_user

    expected_nickname = nickname_formatter(
        expected_nickname_format=expected_nickname,
        roblox_user=(test_group_member.roblox_user if include_roblox_user else None),
        discord_user=(test_group_member.discord_user if include_discord_user else None),
        guild=test_guild,
    )

    return NicknameTestCaseData(
        nickname_fixture=request.param, expected_nickname=expected_nickname
    )
