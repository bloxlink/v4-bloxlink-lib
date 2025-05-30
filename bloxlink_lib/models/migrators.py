from __future__ import annotations
from typing import Type
from bloxlink_lib.models.binds import GuildBind, VALID_BIND_TYPES
from bloxlink_lib.models.schemas.guilds import (  # pylint: disable=no-name-in-module
    GuildRestriction,
)
from bloxlink_lib.models import BaseModel
from bloxlink_lib.models.roblox.binds import RobloxUserNicknames
from pydantic import ValidationInfo
import re


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

    if delete_commands and str(delete_commands).lower() in (
        "none",
        "off",
        "disable",
        "false",
        "0",
    ):
        return False

    return bool(delete_commands)


def migrate_create_missing_roles(create_missing_roles: bool | str) -> bool:
    """Migrate the createMissingRoles field."""

    if isinstance(create_missing_roles, bool):
        return create_missing_roles

    if create_missing_roles.lower() in (
        "disable",
    ):  # keeping track of the "false" values
        return False

    return create_missing_roles


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
            and "verified" in base_model_data.get("joinChannel", {})
            and base_model_data.get("joinChannel", {}).get("verified") is None
        ):
            del base_model_data["joinChannel"]["verified"]

        if (
            base_model_data.get("joinChannel")
            and "unverified" in base_model_data.get("joinChannel", {})
            and base_model_data.get("joinChannel", {}).get("unverified") is None
        ):
            del base_model_data["joinChannel"]["unverified"]

        if (
            base_model_data.get("leaveChannel")
            and "verified" in base_model_data.get("leaveChannel", {})
            and base_model_data.get("leaveChannel", {}).get("verified") is None
        ):
            del base_model_data["leaveChannel"]["verified"]

        if (
            base_model_data.get("leaveChannel")
            and "unverified" in base_model_data.get("leaveChannel", {})
            and base_model_data.get("leaveChannel", {}).get("unverified") is None
        ):
            del base_model_data["leaveChannel"]["unverified"]

        if "joinChannel" in base_model_data and not base_model_data["joinChannel"]:
            del base_model_data["joinChannel"]

        if "leaveChannel" in base_model_data and not base_model_data["leaveChannel"]:
            del base_model_data["leaveChannel"]

    return base_model_data


def migrate_bind_criteria_type(bind_type: VALID_BIND_TYPES | str) -> VALID_BIND_TYPES:
    """Migrate the bind criteria type."""

    if isinstance(bind_type, str):
        bind_type = bind_type.lower()

        if bind_type.startswith("gamep"):
            return "gamepass"

        if bind_type.startswith("grou"):
            return "group"

        if bind_type.startswith("bad"):
            return "badge"

    return bind_type


def migrate_null_values(
    cls: Type[BaseModel], v: str | None, info: ValidationInfo
) -> str:
    """Migrate the null values."""

    if v is None:
        return cls.model_fields[info.field_name].get_default()

    return v


def migrate_nickname_template(nickname_template: str | None) -> str | None:
    """Migrate the nicknameTemplate field.

    If the nicknameTemplate contains a Roblox user nickname template without the curly braces, add them.
    """

    if nickname_template is None:
        return None

    # Special case for {group-rank-GROUPID} templates
    group_rank_id_pattern = re.compile(r"\{group-rank-\d+\}")
    matches = group_rank_id_pattern.findall(nickname_template)

    # Temporarily replace these patterns to protect them
    replacements: dict[str, str] = {}

    for i, match in enumerate(matches):
        placeholder = f"__GROUP_RANK_PLACEHOLDER_{i}__"
        replacements[placeholder] = match
        nickname_template = nickname_template.replace(match, placeholder)

    # Process normal templates
    for template in RobloxUserNicknames:
        if template.value in nickname_template and (
            f"{{{template.value}}}" not in nickname_template
        ):
            nickname_template = nickname_template.replace(
                template.value, f"{{{template.value}}}"
            )

    # Restore the protected patterns
    for placeholder, original in replacements.items():
        nickname_template = nickname_template.replace(placeholder, original)

    return nickname_template


def migrate_binds(guild_binds: list[GuildBind]) -> list[GuildBind]:
    """Migrate the binds field. This will merge duplicate binds."""

    binds_by_hash: dict[int, GuildBind] = {}

    for bind in guild_binds:
        bind_hash = hash(bind)

        if bind_hash not in binds_by_hash:
            binds_by_hash[bind_hash] = bind
        else:
            binds_by_hash[bind_hash].roles.extend(bind.roles)
            binds_by_hash[bind_hash].remove_roles.extend(bind.remove_roles)

    return list(binds_by_hash.values())
