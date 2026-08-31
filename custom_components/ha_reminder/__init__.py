"""HA Reminder integration."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall

from .advanced import AdvancedReminderManager, AdvancedReminderStore
from .const import (
    ADVANCED_PLATFORMS,
    CONF_ENTRY_TYPE,
    ENTRY_TYPE_ADVANCED,
    INTERACTION_ACKNOWLEDGE,
    INTERACTION_COMPLETE,
    INTERACTION_DISMISS,
    INTERACTION_SNOOZE,
    PERSON_PLATFORMS,
    SERVICE_INTERACT,
)
from .const import DOMAIN as DOMAIN
from .manager import ReminderManager
from .storage import ReminderStore

type HAConfigEntry = ConfigEntry[ReminderManager | AdvancedReminderManager]


async def async_setup_entry(hass: HomeAssistant, entry: HAConfigEntry) -> bool:
    """Set up a configured person or advanced reminder device."""
    advanced = entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_ADVANCED
    manager = AdvancedReminderManager(hass, entry) if advanced else ReminderManager(hass, entry)
    await manager.async_start()
    entry.runtime_data = manager
    if advanced:
        hass.data.setdefault(DOMAIN, {}).setdefault("advanced_managers", {})[entry.entry_id] = manager
        _async_register_services(hass)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(
        entry, ADVANCED_PLATFORMS if advanced else PERSON_PLATFORMS
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HAConfigEntry) -> bool:
    """Unload a configured person or advanced reminder device."""
    advanced = entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_ADVANCED
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, ADVANCED_PLATFORMS if advanced else PERSON_PLATFORMS
    )
    if unload_ok:
        await entry.runtime_data.async_stop()
        if advanced:
            hass.data.get(DOMAIN, {}).get("advanced_managers", {}).pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: HAConfigEntry) -> None:
    """Reload a manager after options change so schedules use the new definition."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(hass: HomeAssistant, entry: HAConfigEntry) -> None:
    """Remove integration-owned persisted state when its entry is deleted."""
    if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_ADVANCED:
        await AdvancedReminderStore(hass, entry.entry_id).async_remove()
    else:
        await ReminderStore(hass, entry.entry_id).async_remove()


def _async_register_services(hass: HomeAssistant) -> None:
    """Expose one idempotent interaction action for every advanced reminder."""
    if hass.services.has_service(DOMAIN, SERVICE_INTERACT):
        return

    async def async_interact(call: ServiceCall) -> None:
        if call.data["interaction"] != INTERACTION_COMPLETE:
            return
        manager = hass.data.get(DOMAIN, {}).get("advanced_managers", {}).get(call.data["reminder_id"])
        if manager:
            await manager.async_complete(call.data.get("occurrence_id"))

    hass.services.async_register(
        DOMAIN,
        SERVICE_INTERACT,
        async_interact,
        schema=vol.Schema(
            {
                vol.Required("reminder_id"): str,
                vol.Required("interaction"): vol.In(
                    [
                        INTERACTION_COMPLETE,
                        INTERACTION_SNOOZE,
                        INTERACTION_ACKNOWLEDGE,
                        INTERACTION_DISMISS,
                    ]
                ),
                vol.Optional("occurrence_id"): str,
            }
        ),
    )
