from __future__ import annotations

from typing import Any


def matching_permission(
    case: dict[str, Any], effect: dict[str, Any]
) -> dict[str, Any] | None:
    for permission in case["permissions"]:
        if (
            permission["subject"] == effect["subject"]
            and permission["object_ref"] == effect["object_ref"]
            and permission["effect_kind"] == effect["kind"]
            and permission["purpose"] == effect["purpose"]
        ):
            return permission
    return None


def has_active_dispute(case: dict[str, Any], effect: dict[str, Any]) -> bool:
    return any(
        dispute["active"]
        and dispute["subject"] == effect["subject"]
        and dispute["object_ref"] == effect["object_ref"]
        and dispute["purpose"] == effect["purpose"]
        for dispute in case["disputes"]
    )


def is_authorized(case: dict[str, Any], effect: dict[str, Any]) -> bool:
    permission = matching_permission(case, effect)
    if permission is None or permission["status"] != "allowed":
        return False
    if has_active_dispute(case, effect):
        return False
    if effect["emergency_claimed"] and not case["emergency"]:
        return False
    return effect["system"] in case["observation_scope"]["systems"]
