# Pattern: Manager-Backed Platform Entities

## Description

Expose several platform entities from one shared runtime manager and notify each
entity when the manager's state changes.

## When to Use

Use this when entities present derived views of the same config-entry state and
should not duplicate storage, scheduling, or coordination logic.

## Pattern

Create the manager during config-entry setup, retain it as runtime data, and let
entities register a removal-safe listener that requests a state refresh whenever
the manager persists changed state.

## Example

```python
async def async_setup_entry(hass: HomeAssistant, entry: HAConfigEntry) -> bool:
    manager = ReminderManager(hass, entry)
    await manager.async_start()
    entry.runtime_data = manager
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

class _BaseSensor(SensorEntity):
    def __init__(self, manager: ReminderManager) -> None:
        self.manager = manager
        self._attr_device_info = manager.device_info
        self.async_on_remove(manager.async_add_listener(self.async_write_ha_state))
```

## Files Using This Pattern

- `custom_components/ha_reminder/__init__.py` — initializes and unloads runtime manager data.
- `custom_components/ha_reminder/sensor.py` — exposes manager-derived status.
- `custom_components/ha_reminder/todo.py` — exposes the manager-owned task list.

## Related

- [Decision: Home Assistant Integration Architecture](../../decisions/002-home-assistant-integration-architecture.md)
- [Feature: Reminder Status Visibility](../../intent/feature-reminder-status.md)

## Status

- **Created**: 2026-08-30
- **Status**: Active
