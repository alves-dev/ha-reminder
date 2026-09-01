"""Diagnostic sensors for HA Reminder."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .advanced import AdvancedReminderManager
from .manager import ReminderManager


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    for manager in entry.runtime_data["person_managers"].values():
        async_add_entities(
            [PendingRemindersSensor(manager), NextReminderSensor(manager)],
            config_subentry_id=manager.entry.entry_id,
        )
    for manager in entry.runtime_data["advanced_managers"].values():
        async_add_entities(
            [AdvancedStatusSensor(manager), AdvancedNextOccurrenceSensor(manager)],
            config_subentry_id=manager.entry.entry_id,
        )


class _BaseSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, manager: ReminderManager) -> None:
        self.manager = manager
        self._attr_device_info = manager.device_info
        self.async_on_remove(manager.async_add_listener(self.async_write_ha_state))


class PendingRemindersSensor(_BaseSensor):
    _attr_translation_key = "pending_reminders"
    _attr_icon = "mdi:format-list-checks"

    def __init__(self, manager: ReminderManager) -> None:
        super().__init__(manager)
        self._attr_unique_id = f"{manager.entry.entry_id}_pending_reminders"

    @property
    def native_value(self) -> int:
        return len(self.manager.reminders)


class NextReminderSensor(_BaseSensor):
    _attr_translation_key = "next_reminder"
    _attr_icon = "mdi:clock-alert-outline"

    def __init__(self, manager: ReminderManager) -> None:
        super().__init__(manager)
        self._attr_unique_id = f"{manager.entry.entry_id}_next_reminder"

    @property
    def native_value(self) -> str | None:
        reminder = self.manager.next_reminder
        return reminder.next_notification_at if reminder else None

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        reminder = self.manager.next_reminder
        if not reminder:
            return None
        return {"reminder_id": reminder.reminder_id, "title": reminder.title, "reason": "scheduled"}


class _AdvancedBaseSensor(SensorEntity):
    """Base entity for values derived from an advanced reminder manager."""

    _attr_has_entity_name = True

    def __init__(self, manager: AdvancedReminderManager) -> None:
        self.manager = manager
        self._attr_device_info = manager.device_info
        self.async_on_remove(manager.async_add_listener(self.async_write_ha_state))


class AdvancedStatusSensor(_AdvancedBaseSensor):
    """Expose the conceptual occurrence state of an advanced reminder."""

    _attr_translation_key = "advanced_status"

    def __init__(self, manager: AdvancedReminderManager) -> None:
        super().__init__(manager)
        self._attr_unique_id = f"{manager.entry.entry_id}_advanced_status"

    @property
    def native_value(self) -> str:
        return self.manager.status


class AdvancedNextOccurrenceSensor(_AdvancedBaseSensor):
    """Expose the next scheduled occurrence in UTC."""

    _attr_translation_key = "advanced_next_occurrence"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, manager: AdvancedReminderManager) -> None:
        super().__init__(manager)
        self._attr_unique_id = f"{manager.entry.entry_id}_advanced_next_occurrence"

    @property
    def native_value(self) -> str | None:
        value = self.manager.next_occurrence_at
        return value.isoformat() if value else None
