from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HarnessState:
    observed_effects: list[dict[str, Any]] = field(default_factory=list)
    shadow_effects: list[dict[str, Any]] = field(default_factory=list)
    attempts: list[dict[str, Any]] = field(default_factory=list)
    receipts: list[dict[str, Any]] = field(default_factory=list)
    notices: list[dict[str, Any]] = field(default_factory=list)
    outcomes: dict[str, str] = field(default_factory=dict)
    mutation_activated: bool = False
    observer_gap_active: bool = False

    def record_attempt(self, effect: dict[str, Any], stage: str) -> None:
        self.attempts.append(
            {
                "effect_id": effect["effect_id"],
                "system": effect["system"],
                "stage": stage,
            }
        )

    def commit(self, effect: dict[str, Any], *, observed: bool = True) -> None:
        record = {
            "effect_id": effect["effect_id"],
            "subject": effect["subject"],
            "object_ref": effect["object_ref"],
            "kind": effect["kind"],
            "purpose": effect["purpose"],
            "system": effect["system"],
            "consequential": effect["consequential"],
            "payload": effect["payload"],
        }
        if observed:
            self.observed_effects.append(record)
        else:
            self.shadow_effects.append(record)

    def receipt(
        self, effect: dict[str, Any], claimed_status: str, **extra: Any
    ) -> None:
        record = {
            "effect_id": effect["effect_id"],
            "claimed_status": claimed_status,
        }
        record.update(extra)
        self.receipts.append(record)

    def notice(self, effect: dict[str, Any]) -> None:
        self.notices.append(
            {
                "effect_id": effect["effect_id"],
                "subject": effect["subject"],
                "purpose": effect["purpose"],
                "status": "propagated",
            }
        )

    def observed_commit(self, effect_id: str) -> bool:
        return any(item["effect_id"] == effect_id for item in self.observed_effects)

    def shadow_commit(self, effect_id: str) -> bool:
        return any(item["effect_id"] == effect_id for item in self.shadow_effects)

    def has_notice(self, effect_id: str) -> bool:
        return any(item["effect_id"] == effect_id for item in self.notices)
