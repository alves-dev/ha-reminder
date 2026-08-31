"""Unit tests for configuration, to-do serialization, and reminder lifecycle behavior."""

from datetime import date, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

import pytest
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.ha_reminder.advanced import AdvancedReminderManager
from custom_components.ha_reminder.config_flow import OptionsFlow, _normalise, _normalise_advanced
from custom_components.ha_reminder.manager import ReminderManager
from custom_components.ha_reminder.models import Reminder
from custom_components.ha_reminder.todo import ReminderTodoList


def _manager(hass: HomeAssistant) -> ReminderManager:
    """Create an isolated manager with one available configured channel."""
    entry = SimpleNamespace(
        entry_id="entry-igor",
        data={
            "person_entity_id": "person.igor",
            "intervals": [900, 1800, 3600, 14400],
            "quiet_start": "22:00",
            "quiet_end": "07:00",
            "retry_interval": 300,
            "max_retries": 3,
            "channels": [
                {
                    "id": "mobile",
                    "name": "Mobile",
                    "script_entity_id": "script.reminder_mobile_igor",
                    "enabled": True,
                }
            ],
            "assignments": [
                {"person_entity_id": "person.igor", "channel_id": "mobile", "priority": 1}
            ],
        },
        options={},
    )
    manager = ReminderManager(hass, entry)
    manager.todo = SimpleNamespace(entity_id="todo.reminders_igor")
    manager._async_refresh_configuration_issues = Mock()
    manager._persist_and_schedule = Mock()
    manager._in_quiet_hours = Mock(return_value=False)
    return manager


def _reminder(generation: int = 1) -> Reminder:
    """Return a due reminder ready for an isolated delivery attempt."""
    now = dt_util.utcnow()
    return Reminder(
        item_uid="item-1",
        reminder_id="reminder-1",
        title="Buy pet food",
        description=None,
        due=None,
        created_at=now.isoformat(),
        next_notification_at=now.isoformat(),
        generation=generation,
    )


def _advanced_manager(hass: HomeAssistant) -> AdvancedReminderManager:
    """Create an advanced reminder manager without storage or platform setup."""
    entry = SimpleNamespace(
        entry_id="advanced-oil",
        title="Check car oil",
        data={
            "title": "Check car oil",
            "entry_type": "advanced",
            "recipients": ["person.igor", "person.jade"],
            "level": "high",
            "schedule_type": "daily",
            "start_date": (dt_util.now().date() - timedelta(days=1)).isoformat(),
            "time_period": "morning",
            "exact_time": "09:00",
            "weekdays": [],
            "interval_days": 1,
            "completion_policy": "until_completed",
            "recurrence_reference": "schedule",
            "enabled": True,
        },
        options={},
    )
    manager = AdvancedReminderManager(hass, entry)
    manager._persist_and_schedule = Mock()
    return manager


def test_normalise_converts_intervals_and_retry_minutes() -> None:
    """Human-friendly timing values become persistent seconds."""
    result = _normalise(
        {
            "person_entity_id": "person.igor",
            "intervals": "15m, 1h, 4h",
            "quiet_start": "22:00",
            "quiet_end": "07:00",
            "retry_interval": 5,
            "max_retries": 3,
        }
    )

    assert result["intervals"] == [900, 3600, 14400]
    assert result["retry_interval"] == 300


@pytest.mark.asyncio
async def test_channel_test_failure_uses_description_instead_of_translated_error() -> None:
    """A failed manual test reports its result without a translated base error."""
    entry = SimpleNamespace(
        data={
            "channels": [
                {
                    "id": "mobile",
                    "name": "Mobile",
                    "script_entity_id": "script.reminder_mobile_igor",
                }
            ]
        },
        options={},
        runtime_data=SimpleNamespace(async_test_channel=AsyncMock(return_value=False)),
    )
    flow = OptionsFlow()

    with (
        patch.object(OptionsFlow, "config_entry", new_callable=PropertyMock, return_value=entry),
        patch.object(OptionsFlow, "async_show_form", return_value={}) as show_form,
    ):
        await flow.async_step_test_channel({"channel_id": "mobile"})

    assert show_form.call_args.kwargs["description_placeholders"] == {
        "result": "Failed: the script did not confirm delivery."
    }
    assert "errors" not in show_form.call_args.kwargs


def test_todo_serialization_preserves_date_only_due_value() -> None:
    """Date-only items remain date-only so the manager can use 09:00."""
    todo_item = ReminderTodoList._to_item(
        {
            "uid": "item-1",
            "summary": "Buy pet food",
            "description": None,
            "status": "needs_action",
            "due": "2026-08-30",
        }
    )

    assert todo_item.due == date(2026, 8, 30)
    assert not isinstance(todo_item.due, datetime)


@pytest.mark.asyncio
async def test_successful_initial_delivery_uses_second_progressive_interval(
    hass: HomeAssistant,
) -> None:
    """A successful first cycle advances to the interval after the creation delay."""
    manager = _manager(hass)
    reminder = _reminder()
    manager.reminders[reminder.item_uid] = reminder
    manager._generations[reminder.item_uid] = reminder.generation
    hass.states.async_set("script.reminder_mobile_igor", "off")
    manager._async_try_channels = AsyncMock(return_value=(True, "mobile"))

    before = dt_util.utcnow()
    await manager._async_deliver(reminder.item_uid, reminder.generation)

    assert reminder.notification_cycle == 1
    assert (reminder.next_at - before).total_seconds() >= manager.intervals[1] - 1


@pytest.mark.asyncio
async def test_unavailable_configured_channel_uses_delivery_retry(hass: HomeAssistant) -> None:
    """A configured but unavailable script is a complete delivery failure, not missing setup."""
    manager = _manager(hass)
    reminder = _reminder()
    manager.reminders[reminder.item_uid] = reminder
    manager._generations[reminder.item_uid] = reminder.generation
    hass.states.async_set("script.reminder_mobile_igor", STATE_UNAVAILABLE)
    manager._async_try_channels = AsyncMock(return_value=(False, None))

    before = dt_util.utcnow()
    await manager._async_deliver(reminder.item_uid, reminder.generation)

    assert reminder.delivery_retry_count == 1
    assert (reminder.next_at - before).total_seconds() >= 299
    manager._async_try_channels.assert_awaited_once_with(reminder, [])


@pytest.mark.asyncio
async def test_channel_test_calls_only_selected_script_without_changing_reminders(
    hass: HomeAssistant,
) -> None:
    """A manual channel test uses the script contract without delivery side effects."""
    manager = _manager(hass)
    reminder = _reminder()
    manager.reminders[reminder.item_uid] = reminder
    reminder_snapshot = reminder.as_dict()
    hass.states.async_set("script.reminder_mobile_igor", "off")

    with patch.object(
        type(hass.services), "async_call", new=AsyncMock(return_value={"success": True})
    ) as async_call:
        assert await manager.async_test_channel("mobile")

    async_call.assert_awaited_once()
    assert async_call.await_args.args[:2] == ("script", "reminder_mobile_igor")
    payload = async_call.await_args.args[-1]
    assert payload["reminder_id"].startswith("test-")
    assert payload["person_entity_id"] == "person.igor"
    assert payload["todo_entity_id"] == "todo.reminders_igor"
    assert payload["todo_item_uid"] is None
    assert payload["title"] == "HA Reminder channel test"
    assert payload["description"] == "This is a manual notification-channel test."
    assert payload["level"] == "low"
    assert payload["attempt"] == 1
    assert payload["channel_priority"] == 1
    assert payload["created_at"]
    assert payload["due_at"] is None
    assert payload["is_test"] is True
    assert reminder.as_dict() == reminder_snapshot


@pytest.mark.asyncio
async def test_channel_test_rejects_an_unavailable_script(hass: HomeAssistant) -> None:
    """An unavailable script is reported as a failed test without invoking it."""
    manager = _manager(hass)
    hass.states.async_set("script.reminder_mobile_igor", STATE_UNAVAILABLE)

    with patch.object(type(hass.services), "async_call", new=AsyncMock()) as async_call:
        assert not await manager.async_test_channel("mobile")

    async_call.assert_not_awaited()


@pytest.mark.asyncio
async def test_channel_test_requires_a_success_response(hass: HomeAssistant) -> None:
    """A script response without a successful contract result fails the test."""
    manager = _manager(hass)
    hass.states.async_set("script.reminder_mobile_igor", "off")

    with patch.object(
        type(hass.services), "async_call", new=AsyncMock(return_value={})
    ):
        assert not await manager.async_test_channel("mobile")


@pytest.mark.asyncio
async def test_advanced_delivery_calls_the_response_capable_script_service(
    hass: HomeAssistant,
) -> None:
    """Advanced reminders call the named script service to receive its response."""
    manager = _advanced_manager(hass)
    now = dt_util.utcnow().isoformat()
    manager.store.data = {
        "active": {
            "occurrence_id": "occurrence-1",
            "generation": 1,
            "scheduled_at": now,
            "recipients": {"person.igor": {"retries": 0}},
        }
    }
    channel = {
        "id": "mobile",
        "script_entity_id": "script.reminder_mobile_igor",
        "priority": 1,
    }

    with patch.object(
        type(hass.services), "async_call", new=AsyncMock(return_value={"success": True})
    ) as async_call:
        assert await manager._async_call_channel("person.igor", {}, 1, channel)

    assert async_call.await_args.args[:2] == ("script", "reminder_mobile_igor")
    assert async_call.await_args.args[-1]["reminder_id"] == "occurrence-1"


@pytest.mark.asyncio
async def test_reopened_item_gets_a_new_generation_after_completion(hass: HomeAssistant) -> None:
    """Late work from a completed item cannot match a reopened item with the same UID."""
    manager = _manager(hass)
    reminder = _reminder()
    manager.reminders[reminder.item_uid] = reminder
    manager._generations[reminder.item_uid] = reminder.generation
    item = {
        "uid": reminder.item_uid,
        "summary": reminder.title,
        "description": reminder.description,
        "status": "needs_action",
        "due": reminder.due,
    }

    await manager.async_reconcile([])
    await manager.async_reconcile([item])

    assert manager.reminders[reminder.item_uid].generation == 2


def test_advanced_configuration_rejects_completion_based_expiring_recurrence() -> None:
    """Completion anchoring requires an occurrence that remains active until completion."""
    with pytest.raises(Exception):
        _normalise_advanced(
            {
                "title": "Check car oil",
                "recipients": ["person.igor"],
                "level": "normal",
                "schedule_type": "daily",
                "start_date": "2026-08-30",
                "time_period": "morning",
                "exact_time": "09:00",
                "weekdays": [],
                "interval_days": 1,
                "completion_policy": "expire_at_end_of_day",
                "recurrence_reference": "completion",
                "enabled": True,
            }
        )


@pytest.mark.asyncio
async def test_advanced_occurrence_creates_independent_recipient_cycles(hass: HomeAssistant) -> None:
    """One occurrence shares completion while retaining one delivery state per recipient."""
    manager = _advanced_manager(hass)
    due_at = dt_util.utcnow() - timedelta(seconds=1)
    manager.store.data = {
        "generation": 0,
        "active": None,
        "next_occurrence_at": due_at.isoformat(),
        "last_status": "scheduled",
    }

    await manager._async_advance_occurrence_locked()

    active = manager.store.data["active"]
    assert active is not None
    assert set(active["recipients"]) == {"person.igor", "person.jade"}
    assert all(state["cycle"] == 0 for state in active["recipients"].values())


@pytest.mark.asyncio
async def test_advanced_completion_is_idempotent(hass: HomeAssistant) -> None:
    """Repeated completion cannot recreate or reschedule an already completed occurrence."""
    manager = _advanced_manager(hass)
    now = dt_util.utcnow()
    manager.store.data = {
        "generation": 1,
        "active": {
            "occurrence_id": "occurrence-1",
            "generation": 1,
            "scheduled_at": now.isoformat(),
            "recipients": {"person.igor": {"next_at": now.isoformat(), "cycle": 0, "retries": 0}},
        },
        "next_occurrence_at": None,
        "last_status": "active",
    }

    assert await manager.async_complete("occurrence-1")
    assert not await manager.async_complete("occurrence-1")
    assert manager.store.data["active"] is None
    assert manager.store.data["last_status"] == "completed"


def test_completion_anchored_every_days_uses_completion_date(hass: HomeAssistant) -> None:
    """A completion-based interval starts from completion instead of the original schedule."""
    manager = _advanced_manager(hass)
    manager.data.update(
        {
            "schedule_type": "every_days",
            "interval_days": 60,
            "recurrence_reference": "completion",
            "start_date": "2026-09-01",
        }
    )
    completed_at = dt_util.as_utc(dt_util.as_local(datetime(2026, 9, 20, 10, 0)))

    following = manager._next_schedule(completed_at)

    assert following is not None
    assert dt_util.as_local(following).date() == date(2026, 11, 19)
