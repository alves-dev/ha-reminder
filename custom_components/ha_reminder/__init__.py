"""HA Reminder integration."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigSubentry
from homeassistant.core import EVENT_HOMEASSISTANT_STARTED, HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from .advanced import AdvancedReminderManager, AdvancedReminderStore
from .const import (
    ADVANCED_PLATFORMS,
    CONF_ENTRY_TYPE,
    DOMAIN,
    ENTRY_TYPE_ADVANCED,
    INTERACTION_ACKNOWLEDGE,
    INTERACTION_COMPLETE,
    INTERACTION_DISMISS,
    INTERACTION_SNOOZE,
    PERSON_PLATFORMS,
    SERVICE_INTERACT,
)
from .manager import ReminderManager
from .runtime import ReminderSubentry
from .storage import ReminderStore

PLATFORMS = list(dict.fromkeys([*PERSON_PLATFORMS, *ADVANCED_PLATFORMS]))
type ReminderManagerType = ReminderManager | AdvancedReminderManager
type HAConfigEntry = ConfigEntry[dict[str, dict[str, ReminderManagerType]]]


async def async_setup(hass: HomeAssistant, _config: dict[str, Any]) -> bool:
    """Migrate legacy independent entries before Home Assistant sets them up."""
    await _async_migrate_legacy_entries(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: HAConfigEntry) -> bool:
    """Set up all person and advanced reminder subentries."""
    person_managers: dict[str, ReminderManager] = {}
    advanced_managers: dict[str, AdvancedReminderManager] = {}
    for subentry in entry.subentries.values():
        runtime_entry = ReminderSubentry(hass, entry, subentry)
        if subentry.subentry_type == ENTRY_TYPE_ADVANCED:
            manager = AdvancedReminderManager(hass, runtime_entry)
            advanced_managers[subentry.subentry_id] = manager
        else:
            manager = ReminderManager(hass, runtime_entry)
            person_managers[subentry.subentry_id] = manager
        await manager.async_start()

    entry.runtime_data = {
        "person_managers": person_managers,
        "advanced_managers": advanced_managers,
    }
    hass.data.setdefault(DOMAIN, {})["advanced_managers"] = advanced_managers
    _async_register_services(hass)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: HAConfigEntry) -> bool:
    """Unload all subentry platforms and stop their reminder managers."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        for manager in entry.runtime_data["person_managers"].values():
            await manager.async_stop()
        for manager in entry.runtime_data["advanced_managers"].values():
            await manager.async_stop()
        hass.data.get(DOMAIN, {}).pop("advanced_managers", None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: HAConfigEntry) -> None:
    """Clean removed-subentry state, then reload managers after configuration changes."""
    configured_ids = set(entry.subentries)
    for subentry_id, manager in entry.runtime_data["person_managers"].items():
        if subentry_id not in configured_ids:
            await manager.store.async_remove()
    for subentry_id, manager in entry.runtime_data["advanced_managers"].items():
        if subentry_id not in configured_ids:
            await manager.store.async_remove()
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_entry(hass: HomeAssistant, entry: HAConfigEntry) -> None:
    """Remove all integration-owned state when the parent entry is deleted."""
    for subentry in entry.subentries.values():
        if subentry.subentry_type == ENTRY_TYPE_ADVANCED:
            await AdvancedReminderStore(hass, subentry.subentry_id).async_remove()
        else:
            await ReminderStore(hass, subentry.subentry_id).async_remove()


async def _async_migrate_legacy_entries(hass: HomeAssistant) -> None:
    """Convert independent person and advanced entries into one parent entry."""
    entries = hass.config_entries.async_entries(DOMAIN)
    legacy_entries = [entry for entry in entries if entry.data.get(CONF_ENTRY_TYPE)]
    if not legacy_entries:
        return

    parent = next(
        (entry for entry in entries if not entry.data.get(CONF_ENTRY_TYPE)), legacy_entries[0]
    )
    entity_registry = er.async_get(hass)
    device_registry = dr.async_get(hass)

    for legacy_entry in legacy_entries:
        data = {**legacy_entry.data, **legacy_entry.options}
        subentry = ConfigSubentry(
            data=MappingProxyType(data),
            subentry_id=legacy_entry.entry_id,
            subentry_type=data[CONF_ENTRY_TYPE],
            title=legacy_entry.title,
            unique_id=data.get("person_entity_id"),
        )
        hass.config_entries.async_add_subentry(parent, subentry)
        _async_migrate_registry_entries(
            entity_registry, device_registry, legacy_entry, parent, subentry
        )

    hass.config_entries.async_update_entry(parent, title="HA Reminder", data={}, options={})
    entries_to_remove = [entry.entry_id for entry in legacy_entries if entry != parent]
    if entries_to_remove:
        hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED,
            lambda _event: hass.add_job(
                _async_remove_legacy_entries(hass, entries_to_remove)
            ),
        )


async def _async_remove_legacy_entries(hass: HomeAssistant, entry_ids: list[str]) -> None:
    """Remove legacy entries after startup has released their setup locks."""
    for entry_id in entry_ids:
        if hass.config_entries.async_get_entry(entry_id):
            await hass.config_entries.async_remove(entry_id)


def _async_migrate_registry_entries(
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    legacy_entry: ConfigEntry,
    parent: ConfigEntry,
    subentry: ConfigSubentry,
) -> None:
    """Retain entity and device identities while attaching them to a subentry."""
    for entity in er.async_entries_for_config_entry(entity_registry, legacy_entry.entry_id):
        entity_registry.async_update_entity(
            entity.entity_id,
            config_entry_id=parent.entry_id,
            config_subentry_id=subentry.subentry_id,
        )
    for device in dr.async_entries_for_config_entry(device_registry, legacy_entry.entry_id):
        device_registry.async_update_device(
            device.id,
            new_config_entry_id=parent.entry_id,
            new_config_subentry_id=subentry.subentry_id,
            new_identifiers={(DOMAIN, subentry.subentry_id)},
        )


def _async_register_services(hass: HomeAssistant) -> None:
    """Expose one idempotent interaction action for every advanced reminder."""
    if hass.services.has_service(DOMAIN, SERVICE_INTERACT):
        return

    async def async_interact(call: ServiceCall) -> None:
        if call.data["interaction"] != INTERACTION_COMPLETE:
            return
        manager = hass.data.get(DOMAIN, {}).get("advanced_managers", {}).get(
            call.data["reminder_id"]
        )
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
