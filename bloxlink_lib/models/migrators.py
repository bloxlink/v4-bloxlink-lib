from __future__ import annotations
from bloxlink_lib.models.schemas.guilds import (  # pylint: disable=no-name-in-module
    GuildRestriction,
)
from bloxlink_lib.models import BaseModel


def migrate_restrictions(
    restrictions: dict[str, dict[str, GuildRestriction]],
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

    if delete_commands and delete_commands.lower() in (
        "none",
        "off",
        "disable",
        "false",
        "0",
    ):
        return False

    return bool(delete_commands)


def migrate_dynamic_roles(dynamic_roles: bool | str) -> bool:
    """Migrate the dynamicRoles field."""

    if isinstance(dynamic_roles, bool):
        return dynamic_roles

    if dynamic_roles.lower() in ("disable",):  # keeping track of the "false" values
        return False

    # return dynamic_roles in ()

    return dynamic_roles


def migrate_magic_roles(magic_roles: dict) -> dict:
    """Migrate the magicRoles field."""

    for magic_role_id, magic_role_data in dict(magic_roles).items():
        if magic_role_id == "undefined":
            magic_roles.pop(magic_role_id)
            continue

        if not isinstance(magic_role_data, list):
            magic_roles[magic_role_id] = [magic_role_data]

    return magic_roles


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


def unset_empty_dicts(base_model: BaseModel, base_model_data: dict) -> dict:
    """Remove empty dictionaries from the data before Pydantic validates the model"""

    if isinstance(base_model_data, dict):
        for field_name in base_model.model_fields:
            if (
                isinstance(base_model_data.get(field_name), dict)
                and len(base_model_data[field_name]) == 0
            ):
                del base_model_data[field_name]  # unset the field

    return base_model_data


def unset_empty_joinchannels(base_model: BaseModel, base_model_data: dict) -> dict:
    """Remove empty joinChannels from the data before Pydantic validates the model"""

    if isinstance(base_model_data, dict):
        if (
            base_model_data.get("joinChannel")
            and base_model_data.get("joinChannel").get("verified") is None
        ):
            del base_model_data["joinChannel"]["verified"]

        if (
            base_model_data.get("joinChannel")
            and base_model_data.get("joinChannel").get("unverified") is None
        ):
            del base_model_data["joinChannel"]["unverified"]

        if (
            base_model_data.get("leaveChannel")
            and base_model_data.get("leaveChannel").get("verified") is None
        ):
            del base_model_data["leaveChannel"]["verified"]

        if (
            base_model_data.get("leaveChannel")
            and base_model_data.get("leaveChannel").get("unverified") is None
        ):
            del base_model_data["leaveChannel"]["unverified"]

        if "joinChannel" in base_model_data and not base_model_data["joinChannel"]:
            del base_model_data["joinChannel"]

        if "leaveChannel" in base_model_data and not base_model_data["leaveChannel"]:
            del base_model_data["leaveChannel"]

    return base_model_data
