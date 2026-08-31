"""Storage for HA Reminder state."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY, STORAGE_VERSION


class ReminderStore:
    """Persist data independently of config-entry reloads."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store = Store[dict[str, Any]](hass, STORAGE_VERSION, f"{STORAGE_KEY}.{entry_id}")
        self.data: dict[str, Any] = {"items": {}, "todo_items": [], "generations": {}}

    async def async_load(self) -> None:
        self.data = await self._store.async_load() or {
            "items": {},
            "todo_items": [],
            "generations": {},
        }
        self.data.setdefault("items", {})
        self.data.setdefault("todo_items", [])
        self.data.setdefault("generations", {})

    def async_save(self) -> None:
        self._store.async_delay_save(lambda: self.data, 1)

    async def async_remove(self) -> None:
        await self._store.async_remove()
