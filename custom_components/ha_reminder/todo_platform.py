"""Set up the integration-owned todo platform."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .manager import ReminderManager


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[ReminderManager],
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([entry.runtime_data.todo])
