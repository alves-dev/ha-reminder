"""Enable switch for advanced reminder devices."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .advanced import AdvancedReminderManager


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the advanced-reminder enable switch."""
    for manager in entry.runtime_data["advanced_managers"].values():
        async_add_entities([AdvancedReminderSwitch(manager)], config_subentry_id=manager.entry.entry_id)


class AdvancedReminderSwitch(SwitchEntity):
    """Cancel an active advanced occurrence when the reminder is disabled."""

    _attr_has_entity_name = True
    _attr_translation_key = "advanced_enabled"

    def __init__(self, manager: AdvancedReminderManager) -> None:
        self.manager = manager
        self._attr_unique_id = f"{manager.entry.entry_id}_advanced_enabled"
        self._attr_device_info = manager.device_info
        self.async_on_remove(manager.async_add_listener(self.async_write_ha_state))

    @property
    def is_on(self) -> bool:
        return self.manager.is_enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.manager.async_set_enabled(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.manager.async_set_enabled(False)
