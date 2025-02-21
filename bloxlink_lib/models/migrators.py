from __future__ import annotations
from bloxlink_lib.models.schemas.guilds import (  # pylint: disable=no-name-in-module
    GuildRestriction,
)
from bloxlink_lib.models import BaseModel


def migrate_restrictions(
    restrictions: dict[str, dict[str, GuildRestriction]]
) -> list[GuildRestriction]:
    """Migrate the restrictions field."""

    if isinstance(restrictions, list):
        return restrictions

    new_guild_restrictions: list[GuildRestriction] = []

    for restriction_type, restriction_data in restrictions.items():
        for restricted_id, restriction in restriction_data.items():
            new_guild_restrictions.append(
                GuildRestriction(
                    id=restricted_id,
                    displayName=restriction["name"],
                    addedBy=restriction["addedBy"],
                    reason=restriction.get("reason"),
                    type=restriction_type,
                )
            )

    return new_guild_restrictions


def migrate_delete_commands(delete_commands: int | None | bool) -> bool:
    """Migrate the deleteCommands field."""

    return bool(delete_commands)


def migrate_disallow_ban_evaders(disallow_ban_evaders: bool | str | None) -> bool:
    """Migrate the disallowBanEvaders field."""

    if isinstance(disallow_ban_evaders, bool):
        return disallow_ban_evaders

    return disallow_ban_evaders in ("ban", "kick")


def unset_nulls(base_model: BaseModel, base_model_data: dict) -> dict:
    """Remove null fields from the data before Pydantic validates the model"""

    if isinstance(base_model_data, dict):
        for field_name in base_model.model_fields:
            if field_name in base_model_data and base_model_data[field_name] is None:
                del base_model_data[field_name]  # unset the field

    return base_model_data
