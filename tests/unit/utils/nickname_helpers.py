from bloxlink_lib.models.base.serializable import MemberSerializable, GuildSerializable
from bloxlink_lib.models.roblox.users import RobloxUser
from pydantic import BaseModel


class NicknameTestData(BaseModel):
    """Represents a scenario for a user's nickname"""

    nickname_template: str
    expected_nickname: str | None
    valid_roblox_user: bool
    valid_discord_user: bool


def nickname_formatter(
    expected_nickname_format: str | None = None,
    roblox_user: RobloxUser | None = None,
    discord_user: MemberSerializable | None = None,
    guild: GuildSerializable | None = None,
) -> str | None:
    """Nickname formatter utility."""

    if not expected_nickname_format:
        return None

    return expected_nickname_format.format(
        roblox_user=roblox_user, discord_user=discord_user, guild=guild
    )
