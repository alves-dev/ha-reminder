"""Coverage for integration boundaries and policy branches."""

from datetime import date, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
import voluptuous as vol
from homeassistant.util import dt as dt_util

from custom_components.ha_reminder import async_setup_entry, async_unload_entry
from custom_components.ha_reminder.advanced import AdvancedReminderStore
from custom_components.ha_reminder.config_flow import (
    _normalise,
    _normalise_advanced,
)
from custom_components.ha_reminder.const import (
    CONF_CONTINUE_AFTER_EXACT_TIME,
    CONF_INTERVAL_DAYS,
    CONF_RECURRENCE_REFERENCE,
    CONF_SCHEDULE_TYPE,
    CONF_START_DATE,
    DOMAIN,
    PERIOD_EXACT,
    REFERENCE_COMPLETION,
    SCHEDULE_EVERY_DAYS,
    SCHEDULE_ONCE,
    SCHEDULE_WEEKLY,
)
from custom_components.ha_reminder.manager import ReminderManager
from custom_components.ha_reminder.models import Reminder
from custom_components.ha_reminder.runtime import ReminderSubentry
from custom_components.ha_reminder.sensor import (
    AdvancedNextOccurrenceSensor,
    AdvancedNotificationLevelSensor,
    AdvancedStatusSensor,
    NextReminderSensor,
    PendingRemindersSensor,
)
from custom_components.ha_reminder.switch import (
    AdvancedCompletedTodaySwitch,
    AdvancedReminderSwitch,
)
from custom_components.ha_reminder.todo import ReminderTodoList


def test_manager_properties_and_timing_helpers(hass) -> None:
    """Expose stable identity and convert both supported due formats."""
    entry = SimpleNamespace(
        entry_id="person-entry",
        data={"person_entity_id": "person.jane", "intervals": [60, 120]},
        options={},
    )
    manager = ReminderManager(hass, entry)
    reminder = Reminder(
        "uid", "rid", "Title", "Description", None,
        dt_util.utcnow().isoformat(), dt_util.utcnow().isoformat(),
    )
    manager.reminders["uid"] = reminder

    assert manager.person_name == "Jane"
    assert manager.device_info["name"] == "Reminders — Jane"
    assert manager.next_reminder is reminder
    assert manager._parse_due(None) is None
    assert manager._parse_due("2026-10-19") == dt_util.as_utc(
        dt_util.as_local(datetime(2026, 10, 19, 9))
    )
    assert manager._parse_due("2026-10-19T12:00:00") is not None
    assert manager._configured_channels() == []


@pytest.mark.asyncio
async def test_manager_start_stop_restores_store_and_timers(hass) -> None:
    """Startup rebuilds the todo boundary and stop cancels its timer."""
    from tests.test_config_and_todo import _manager

    manager = _manager(hass)
    manager.store.async_load = AsyncMock()
    manager.store.data = {"items": {}, "todo_items": [], "generations": {}}
    manager.async_reconcile = AsyncMock()
    await manager.async_start()
    assert manager.todo.name == "To-do list"
    timer_cancel = Mock()
    manager._timer_cancel = timer_cancel
    await manager.async_stop()
    assert manager._stopped is True
    timer_cancel.assert_called_once_with()


@pytest.mark.asyncio
async def test_manager_channel_priority_fallback_and_response_validation(hass) -> None:
    """Equal priorities rotate and fallback stops at the first success."""
    from tests.test_config_and_todo import _manager, _reminder

    manager = _manager(hass)
    reminder = _reminder()
    first = {"id": "first", "priority": 1, "script_entity_id": "script.first"}
    second = {"id": "second", "priority": 1, "script_entity_id": "script.second"}
    manager._async_call_channel = AsyncMock(side_effect=[False, True])
    assert await manager._async_try_channels(reminder, [first, second]) == (True, "second")
    manager._async_call_channel.assert_has_awaits([((reminder, first),), ((reminder, second),)])
    manager._async_call_channel_script = AsyncMock(return_value=True)
    assert await manager._async_invoke_channel(first, {"title": "test"})


@pytest.mark.asyncio
async def test_manager_delivery_handles_quiet_hours_missing_config_and_stale_generation(hass) -> None:
    """Delivery suppresses quiet-hour work and ignores stale background results."""
    from tests.test_config_and_todo import _manager, _reminder

    manager = _manager(hass)
    reminder = _reminder()
    manager.reminders[reminder.item_uid] = reminder
    manager._generations[reminder.item_uid] = reminder.generation
    manager._in_quiet_hours = Mock(return_value=True)
    await manager._async_deliver(reminder.item_uid, reminder.generation)
    assert reminder.next_at > dt_util.utcnow()
    await manager._async_deliver(reminder.item_uid, reminder.generation + 1)
    manager._in_quiet_hours = Mock(return_value=False)
    manager.data["channels"] = []
    await manager._async_deliver(reminder.item_uid, reminder.generation)
    assert reminder.next_at > dt_util.utcnow()


@pytest.mark.asyncio
async def test_setup_and_unload_forward_platforms_and_stop_managers(hass) -> None:
    """Parent setup starts both manager types and unload stops them."""
    person_manager = SimpleNamespace(async_start=AsyncMock(), async_stop=AsyncMock())
    advanced_manager = SimpleNamespace(async_start=AsyncMock(), async_stop=AsyncMock())
    person_subentry = SimpleNamespace(subentry_id="person", subentry_type="person", data={})
    advanced_subentry = SimpleNamespace(subentry_id="advanced", subentry_type="advanced", data={})
    entry = SimpleNamespace(
        title="HA Reminder",
        domain=DOMAIN,
        entry_id="parent",
        subentries={"person": person_subentry, "advanced": advanced_subentry},
        async_on_unload=Mock(),
        add_update_listener=Mock(return_value=Mock()),
    )
    with (
        patch("custom_components.ha_reminder.ReminderSubentry", side_effect=lambda *args: args[2]),
        patch("custom_components.ha_reminder.ReminderManager", return_value=person_manager),
        patch("custom_components.ha_reminder.AdvancedReminderManager", return_value=advanced_manager),
        patch.object(hass.config_entries, "async_forward_entry_setups", new=AsyncMock()),
        patch.object(hass.config_entries, "async_unload_platforms", new=AsyncMock(return_value=True)),
    ):
        assert await async_setup_entry(hass, entry) is True
        assert await async_unload_entry(hass, entry) is True
    person_manager.async_start.assert_awaited_once()
    advanced_manager.async_start.assert_awaited_once()
    person_manager.async_stop.assert_awaited_once()
    advanced_manager.async_stop.assert_awaited_once()


@pytest.mark.asyncio
async def test_todo_mutations_keep_uid_and_notify(hass) -> None:
    """Create, update, and delete use the native to-do boundary callback."""
    changed = AsyncMock()
    todo = ReminderTodoList(hass, "entry", "person.jane", "Jane", [], changed)
    with patch.object(todo, "async_write_ha_state"):
        await todo.async_create_todo_item(
            SimpleNamespace(
                uid=None,
                summary="Task",
                description="Details",
                status="needs_action",
                due=date(2026, 10, 19),
            )
        )
    uid = todo._items[0]["uid"]
    with patch.object(todo, "async_write_ha_state"):
        await todo.async_update_todo_item(
            SimpleNamespace(
                uid=uid,
                summary="Updated",
                description=None,
                status="completed",
                due=None,
            )
        )
        await todo.async_delete_todo_items([uid])

    assert todo.todo_items == []
    assert changed.await_count == 3
    await todo.async_update_todo_item(SimpleNamespace(uid=None, summary="ignored"))
    assert changed.await_count == 3


def test_entity_views_and_listener_cleanup(hass) -> None:
    """Person and advanced entities expose manager values and unregister safely."""
    reminder = Reminder(
        "uid", "rid", "Task", "Description", None,
        dt_util.utcnow().isoformat(), dt_util.utcnow().isoformat(),
    )
    person = SimpleNamespace(
        entry=SimpleNamespace(entry_id="person"),
        device_info={"name": "device"},
        reminders={"uid": reminder},
        next_reminder=reminder,
        async_add_listener=Mock(return_value=lambda: None),
    )
    pending = PendingRemindersSensor(person)
    next_sensor = NextReminderSensor(person)
    assert pending.native_value == 1
    assert next_sensor.native_value == reminder.next_notification_at
    assert next_sensor.extra_state_attributes["title"] == "Task"
    person.next_reminder = None
    assert next_sensor.native_value is None
    assert next_sensor.extra_state_attributes is None

    advanced = SimpleNamespace(
        entry=SimpleNamespace(entry_id="advanced"),
        device_info={"name": "advanced"},
        status="active",
        next_occurrence_at=dt_util.utcnow(),
        notification_level="high",
        async_add_listener=Mock(return_value=lambda: None),
    )
    assert AdvancedStatusSensor(advanced).native_value == "active"
    assert AdvancedNextOccurrenceSensor(advanced).native_value
    assert AdvancedNotificationLevelSensor(advanced).native_value == "high"


@pytest.mark.asyncio
async def test_switch_entities_delegate_to_manager(hass) -> None:
    """Both advanced switches delegate state changes to their manager."""
    manager = SimpleNamespace(
        entry=SimpleNamespace(entry_id="advanced"),
        device_info={"name": "advanced"},
        is_enabled=True,
        is_completed_today=False,
        async_add_listener=Mock(return_value=lambda: None),
        async_set_enabled=AsyncMock(),
        async_set_completed_today=AsyncMock(),
    )
    enabled = AdvancedReminderSwitch(manager)
    completed = AdvancedCompletedTodaySwitch(manager)
    assert enabled.is_on is True
    assert completed.is_on is False
    await enabled.async_turn_off()
    await completed.async_turn_on()
    manager.async_set_enabled.assert_awaited_once_with(False)
    manager.async_set_completed_today.assert_awaited_once_with(True)


def test_normalise_rejects_bad_intervals_and_normalises_advanced_values() -> None:
    """Invalid boundary values fail loudly and legacy levels become canonical."""
    with pytest.raises(vol.Invalid):
        _normalise({"intervals": "bad", "retry_interval": 5})
    values = {
        "title": "  Take medicine  ",
        "recipients": ["person.jane"],
        "level": "low",
        "schedule_type": SCHEDULE_ONCE,
        "start_date": "2026-10-20",
        "time_period": PERIOD_EXACT,
        "exact_time": "08:30",
        "completion_policy": "until_completed",
        CONF_CONTINUE_AFTER_EXACT_TIME: False,
    }
    result = _normalise_advanced(values)
    assert result["title"] == "  Take medicine  "
    assert result["level"] == "normal"
    assert result[CONF_CONTINUE_AFTER_EXACT_TIME] is False


def test_advanced_schedule_branches(hass) -> None:
    """Schedule resolution handles once, completion-anchored and weekly rules."""
    from tests.test_config_and_todo import _advanced_manager

    manager = _advanced_manager(hass)
    reference = dt_util.as_local(datetime(2026, 10, 19, 10)).astimezone(dt_util.UTC)
    manager.data.update({CONF_START_DATE: "2026-10-18", CONF_SCHEDULE_TYPE: SCHEDULE_ONCE})
    assert manager._next_schedule(reference) is None
    manager.data.update(
        {
            CONF_SCHEDULE_TYPE: SCHEDULE_EVERY_DAYS,
            CONF_START_DATE: "2026-10-19",
            CONF_INTERVAL_DAYS: 2,
            CONF_RECURRENCE_REFERENCE: REFERENCE_COMPLETION,
        }
    )
    assert manager._next_schedule(reference) > reference
    manager.data.update({CONF_SCHEDULE_TYPE: SCHEDULE_WEEKLY, "weekdays": []})
    assert manager._next_schedule(reference) is not None


@pytest.mark.asyncio
async def test_manager_delivery_failure_rolls_over_after_retries(hass) -> None:
    """Failed deliveries retry, then restart from the first progressive interval."""
    from tests.test_config_and_todo import _manager, _reminder

    manager = _manager(hass)
    manager.data["max_retries"] = 1
    reminder = _reminder()
    manager.reminders[reminder.item_uid] = reminder
    manager._generations[reminder.item_uid] = reminder.generation
    manager._async_try_channels = AsyncMock(return_value=(False, None))
    await manager._async_deliver(reminder.item_uid, reminder.generation)
    assert reminder.delivery_retry_count == 1
    await manager._async_deliver(reminder.item_uid, reminder.generation)
    assert reminder.delivery_retry_count == 0
    assert reminder.notification_cycle == 0


def test_runtime_subentry_delegates_updates(hass) -> None:
    """Runtime subentries expose immutable options and persist data changes."""
    parent = SimpleNamespace()
    subentry = SimpleNamespace(subentry_id="sub", data={"title": "Title"})
    hass.config_entries.async_update_subentry = Mock()
    runtime = ReminderSubentry(hass, parent, subentry)
    assert runtime.entry_id == "sub"
    assert runtime.data["title"] == "Title"
    assert runtime.options == {}
    runtime.async_update_data({"title": "Updated"})
    hass.config_entries.async_update_subentry.assert_called_once_with(parent, subentry, data={"title": "Updated"})


@pytest.mark.asyncio
async def test_advanced_store_load_fills_new_fields(hass) -> None:
    """Older advanced storage records receive defaults for newly added fields."""
    store = AdvancedReminderStore(hass, "advanced")
    with patch.object(store._store, "async_load", new=AsyncMock(return_value={"active": None})):
        await store.async_load()
    assert store.data["generation"] == 0
    assert store.data["last_status"] == "scheduled"
    assert store.data["completed_on"] is None

