"""Runtime views over HA Reminder config subentries."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import HomeAssistant


@dataclass(slots=True)
class ReminderSubentry:
    """Expose a config subentry through the fields used by reminder managers."""

    hass: HomeAssistant
    parent_entry: ConfigEntry
    subentry: ConfigSubentry

    @property
    def entry_id(self) -> str:
        """Return the stable identifier used for runtime persistence."""
        return self.subentry.subentry_id

    @property
    def data(self) -> Mapping[str, Any]:
        """Return the subentry's durable configuration."""
        return self.subentry.data

    @property
    def options(self) -> Mapping[str, Any]:
        """Subentries keep their complete configuration in their data mapping."""
        return {}

    def async_update_data(self, data: Mapping[str, Any]) -> None:
        """Persist an in-place setting change for this subentry."""
        self.hass.config_entries.async_update_subentry(
            self.parent_entry, self.subentry, data=data
        )
