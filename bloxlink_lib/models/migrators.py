from __future__ import annotations

from bloxlink_lib.models.schemas.guilds.guild_types import GuildRestriction


def migrate_restrictions(
    restrictions: dict[str, dict[str, guilds.GuildRestriction]]
) -> list[guilds.GuildRestriction]:
    if isinstance(restrictions, list):
        return restrictions

    new_guild_restrictions: list[GuildRestriction] = []

    for restriction_type, restriction_data in restrictions.items():
        for restricted_id, restriction in restriction_data.items():
            new_guild_restrictions.append(
                guilds.GuildRestriction(
                    id=restricted_id,
                    displayName=restriction["name"],
                    addedBy=restriction["addedBy"],
                    reason=restriction.get("reason"),
                    type=restriction_type,
                )
            )

    return new_guild_restrictions


def migrate_delete_commands(delete_commands: int | None | bool) -> bool:
    return bool(delete_commands)
