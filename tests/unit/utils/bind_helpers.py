from bloxlink_lib.models.base.serializable import MemberSerializable, GuildSerializable
from bloxlink_lib import RobloxUser


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
