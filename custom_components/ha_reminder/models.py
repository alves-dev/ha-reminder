"""Persistent reminder models."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class Reminder:
    """The delivery state of one pending to-do item."""

    item_uid: str
    reminder_id: str
    title: str
    description: str | None
    due: str | None
    created_at: str
    next_notification_at: str
    generation: int = 1
    notification_cycle: int = 0
    delivery_retry_count: int = 0
    last_attempt_at: str | None = None
    last_delivered_at: str | None = None
    last_successful_channel_id: str | None = None

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Reminder:
        return cls(**value)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def next_at(self) -> datetime:
        return datetime.fromisoformat(self.next_notification_at)
