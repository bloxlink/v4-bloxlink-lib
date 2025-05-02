import pytest
from collections import namedtuple
from tests.unit.utils.nickname_helpers import NicknameTestData, nickname_formatter

# fixtures
from .users import test_discord_user_1
from .roblox_users import test_roblox_user_1
from .guilds import test_guild_1

NicknameTestCaseData = namedtuple(
    "NicknameTestCaseData", ["nickname_fixture", "expected_nickname"]
)


@pytest.fixture(
    params=[
        NicknameTestData(
            nickname_template="{roblox-name}",
            expected_nickname="{roblox_user.username}",
            valid_roblox_user=True,
            valid_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{roblox-id}",
            expected_nickname="{roblox_user.id}",
            valid_roblox_user=True,
            valid_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{display-name}",
            expected_nickname="{roblox_user.display_name}",
            valid_roblox_user=True,
            valid_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{smart-name}",
            expected_nickname="{roblox_user.display_name} (@{roblox_user.username})",
            valid_roblox_user=True,
            valid_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{roblox-age}",
            expected_nickname="{roblox_user.age_days}",
            valid_roblox_user=True,
            valid_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{disable-nicknaming}",
            expected_nickname=None,
            valid_roblox_user=True,
            valid_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{group-rank}",
            expected_nickname="Guest",
            valid_roblox_user=True,
            valid_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{discord-name}",
            expected_nickname="{discord_user.username}",
            valid_roblox_user=True,
            valid_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{discord-nick}",
            expected_nickname="{discord_user.nickname}",
            valid_roblox_user=True,
            valid_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{discord-global-name}",
            expected_nickname="{discord_user.global_name}",
            valid_roblox_user=True,
            valid_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="{discord-id}",
            expected_nickname="{discord_user.id}",
            valid_roblox_user=True,
            valid_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="[{group-rank}] {roblox-name}",
            expected_nickname="[Guest] {roblox_user.username}",
            valid_roblox_user=True,
            valid_discord_user=True,
        ),
        NicknameTestData(
            nickname_template="[{group-rank}] {roblox-name} {roblox-id}",
            expected_nickname="[Guest] {roblox_user.username} {roblox_user.id}",
            valid_roblox_user=True,
            valid_discord_user=True,
        ),
    ]
)
def nickname_test_data(
    request, test_roblox_user_1, test_discord_user_1
) -> NicknameTestCaseData:
    expected_nickname = request.param.expected_nickname
    valid_roblox_user = request.param.valid_roblox_user
    valid_discord_user = request.param.valid_discord_user

    expected_nickname = nickname_formatter(
        expected_nickname_format=expected_nickname,
        roblox_user=test_roblox_user_1 if valid_roblox_user else None,
        discord_user=test_discord_user_1 if valid_discord_user else None,
    )

    return NicknameTestCaseData(
        nickname_fixture=request.param, expected_nickname=expected_nickname
    )


@pytest.fixture(
    params=[
        # No Roblox ID linked (unverified)
        NicknameTestData(
            nickname_template="{prefix}",
            expected_nickname="/",
            valid_roblox_user=False,
            valid_discord_user=True,
        ),
    ]
)
def generic_template_test_data(request) -> NicknameTestCaseData:
    expected_nickname = request.param.expected_nickname
    valid_roblox_user = request.param.valid_roblox_user
    valid_discord_user = request.param.valid_discord_user

    expected_nickname = nickname_formatter(
        expected_nickname_format=expected_nickname,
        roblox_user=test_roblox_user_1 if valid_roblox_user else None,
        discord_user=test_discord_user_1 if valid_discord_user else None,
    )

    return NicknameTestCaseData(
        nickname_fixture=request.param, expected_nickname=expected_nickname
    )
