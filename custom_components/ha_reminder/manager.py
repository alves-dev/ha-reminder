"""Scheduling, delivery and reconciliation for simple reminders."""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from datetime import date, datetime, time, timedelta
from typing import Any
from uuid import uuid4

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.issue_registry import (
    IssueSeverity,
    async_create_issue,
    async_delete_issue,
)
from homeassistant.util import dt as dt_util

from .const import (
    CHANNEL_COOLDOWN,
    CHANNEL_TIMEOUT,
    CONF_ASSIGNMENTS,
    CONF_CHANNELS,
    CONF_INTERVALS,
    CONF_MAX_RETRIES,
    CONF_PERSON_ENTITY_ID,
    CONF_QUIET_END,
    CONF_QUIET_START,
    CONF_RETRY_INTERVAL,
    DEFAULT_INTERVALS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_INTERVAL,
    DOMAIN,
    MORNING_TIME,
)
from .models import Reminder
from .storage import ReminderStore
from .todo import ReminderTodoList

_LOGGER = logging.getLogger(__name__)


class ReminderManager:
    """Own all state for one configured person and serialize its delivery work."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.data = {**entry.data, **entry.options}
        self.person_entity_id = self.data[CONF_PERSON_ENTITY_ID]
        self.person_name = self.person_entity_id.split(".", 1)[-1].replace("_", " ").title()
        self.store = ReminderStore(hass, entry.entry_id)
        self.reminders: dict[str, Reminder] = {}
        self._generations: dict[str, int] = {}
        self.todo: ReminderTodoList
        self._listeners: list[Callable[[], None]] = []
        self._timer_cancel: CALLBACK_TYPE | None = None
        self._lock = asyncio.Lock()
        self._stopped = False
        # Dispatch state lives at integration scope: a script shared by people
        # still receives at most one invocation every five seconds.
        dispatcher = hass.data.setdefault(
            DOMAIN, {"channel_locks": defaultdict(asyncio.Lock), "channel_last_call": {}}
        )
        self._channel_locks = dispatcher["channel_locks"]
        self._channel_last_call = dispatcher["channel_last_call"]
        self._round_robin: defaultdict[int, int] = defaultdict(int)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=f"Reminders — {self.person_name}",
            manufacturer="HA Reminder",
            model="Person reminder configuration",
        )

    @property
    def next_reminder(self) -> Reminder | None:
        return min(self.reminders.values(), key=lambda item: item.next_at, default=None)

    def async_add_listener(self, listener: Callable[[], None]) -> CALLBACK_TYPE:
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener) if listener in self._listeners else None

    async def async_start(self) -> None:
        """Restore state and reconcile it with the persisted local todo list."""
        await self.store.async_load()
        self.reminders = {
            uid: Reminder.from_dict(value) for uid, value in self.store.data["items"].items()
        }
        self._generations = {
            uid: int(generation) for uid, generation in self.store.data["generations"].items()
        }
        for uid, reminder in self.reminders.items():
            self._generations[uid] = max(self._generations.get(uid, 0), reminder.generation)
        self.todo = ReminderTodoList(
            self.hass,
            self.entry.entry_id,
            self.person_entity_id,
            self.person_name,
            self.store.data["todo_items"],
            self.async_reconcile,
        )
        await self.async_reconcile(self.store.data["todo_items"])

    async def async_stop(self) -> None:
        """Stop timers and invalidate pending work during an entry unload."""
        self._stopped = True
        if self._timer_cancel:
            self._timer_cancel()
            self._timer_cancel = None

    async def async_reconcile(self, items: list[dict[str, Any]]) -> None:
        """Apply creation, edits, completion and removal lifecycle rules."""
        async with self._lock:
            now = dt_util.utcnow()
            pending = {item["uid"]: item for item in items if item.get("status") == "needs_action"}
            for uid in set(self.reminders) - set(pending):
                self._generations[uid] = self.reminders.pop(uid).generation
            for uid, item in pending.items():
                existing = self.reminders.get(uid)
                if existing is None or self._changed(existing, item):
                    generation = self._next_generation(uid, existing)
                    self.reminders[uid] = self._new_reminder(
                        item, now, generation
                    )
                    _LOGGER.debug("Reminder item %s created or restarted", uid)
            self._async_refresh_configuration_issues()
            self._persist_and_schedule()

    def _next_generation(self, uid: str, existing: Reminder | None) -> int:
        """Return a generation that cannot match invalidated work for this item."""
        previous = max(self._generations.get(uid, 0), existing.generation if existing else 0)
        generation = previous + 1
        self._generations[uid] = generation
        return generation

    @staticmethod
    def _changed(reminder: Reminder, item: dict[str, Any]) -> bool:
        return any(
            (
                reminder.title != item.get("summary"),
                reminder.description != item.get("description"),
                reminder.due != item.get("due"),
            )
        )

    def _new_reminder(self, item: dict[str, Any], now: datetime, generation: int) -> Reminder:
        due_at = self._parse_due(item.get("due"))
        first_at = due_at if due_at else now + timedelta(seconds=self.intervals[0])
        return Reminder(
            item_uid=item["uid"],
            reminder_id=str(uuid4()),
            title=item["summary"],
            description=item.get("description"),
            due=item.get("due"),
            created_at=now.isoformat(),
            next_notification_at=first_at.isoformat(),
            generation=generation,
        )

    def _parse_due(self, raw_due: str | None) -> datetime | None:
        if not raw_due:
            return None
        if "T" in raw_due or " " in raw_due:
            parsed = datetime.fromisoformat(raw_due)
            return dt_util.as_utc(parsed if parsed.tzinfo else dt_util.as_local(parsed))
        # Todo date-only values use the specified 09:00 local morning reference.
        local = datetime.combine(date.fromisoformat(raw_due), time.fromisoformat(MORNING_TIME))
        return dt_util.as_utc(dt_util.as_local(local))

    @property
    def intervals(self) -> list[int]:
        return self.data.get(CONF_INTERVALS, DEFAULT_INTERVALS)

    def _persist_and_schedule(self) -> None:
        self.store.data["items"] = {uid: item.as_dict() for uid, item in self.reminders.items()}
        self.store.data["generations"] = self._generations
        self.store.async_save()
        self._schedule_next()
        for listener in list(self._listeners):
            listener()

    def _schedule_next(self) -> None:
        if self._timer_cancel:
            self._timer_cancel()
            self._timer_cancel = None
        next_item = self.next_reminder
        if next_item:
            when = max(next_item.next_at, dt_util.utcnow())
            self._timer_cancel = async_track_point_in_utc_time(self.hass, self._async_timer, when)

    async def _async_timer(self, _now: datetime) -> None:
        async with self._lock:
            self._timer_cancel = None
            due = sorted(
                (item for item in self.reminders.values() if item.next_at <= dt_util.utcnow()),
                key=lambda item: (item.next_at, item.reminder_id),
            )
        await asyncio.gather(*(self._async_deliver(item.item_uid, item.generation) for item in due))
        async with self._lock:
            self._schedule_next()

    async def _async_deliver(self, uid: str, generation: int) -> None:
        async with self._lock:
            reminder = self.reminders.get(uid)
            if self._stopped or not reminder or reminder.generation != generation:
                return
            if self._in_quiet_hours(dt_util.now()):
                reminder.next_notification_at = self._quiet_end(dt_util.now()).isoformat()
                _LOGGER.debug("Reminder %s suppressed by quiet hours", reminder.reminder_id)
                self._persist_and_schedule()
                return
            configured_channels = self._configured_channels()
            self._async_refresh_configuration_issues(configured_channels)
            if not configured_channels:
                # Missing configuration is neither a failed delivery nor a retry.
                reminder.next_notification_at = (
                    dt_util.utcnow() + timedelta(minutes=5)
                ).isoformat()
                self._persist_and_schedule()
                return
            channels = self._available_channels(configured_channels)
        success, channel_id = await self._async_try_channels(reminder, channels)
        async with self._lock:
            current = self.reminders.get(uid)
            if self._stopped or not current or current.generation != generation:
                return
            if success is None:
                # A queued call reached quiet hours. It was never an actual delivery attempt.
                current.next_notification_at = self._quiet_end(dt_util.now()).isoformat()
                self._persist_and_schedule()
                return
            current.last_attempt_at = dt_util.utcnow().isoformat()
            if success:
                current.last_delivered_at = current.last_attempt_at
                current.last_successful_channel_id = channel_id
                current.delivery_retry_count = 0
                current.notification_cycle += 1
                interval = self.intervals[
                    min(current.notification_cycle, len(self.intervals) - 1)
                ]
                current.next_notification_at = (
                    dt_util.utcnow() + timedelta(seconds=interval)
                ).isoformat()
            else:
                current.delivery_retry_count += 1
                if current.delivery_retry_count <= self.data.get(
                    CONF_MAX_RETRIES, DEFAULT_MAX_RETRIES
                ):
                    delay = self.data.get(CONF_RETRY_INTERVAL, DEFAULT_RETRY_INTERVAL)
                else:
                    current.delivery_retry_count = 0
                    delay = self.intervals[0]
                current.next_notification_at = (
                    dt_util.utcnow() + timedelta(seconds=delay)
                ).isoformat()
            self._persist_and_schedule()

    def _configured_channels(self) -> list[dict[str, Any]]:
        """Return enabled assigned channels, including temporarily unavailable scripts."""
        channels = {
            item["id"]: item
            for item in self.data.get(CONF_CHANNELS, [])
            if item.get("enabled", True)
        }
        output = []
        for assignment in self.data.get(CONF_ASSIGNMENTS, []):
            if assignment.get("person_entity_id") != self.person_entity_id:
                continue
            channel = channels.get(assignment.get("channel_id"))
            if channel:
                output.append({**channel, "priority": int(assignment.get("priority", 1))})
        return output

    def _available_channels(self, configured_channels: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Return configured channels whose script can currently be called."""
        return [
            channel
            for channel in configured_channels
            if (state := self.hass.states.get(channel["script_entity_id"])) is not None
            and state.state != STATE_UNAVAILABLE
        ]

    def _async_refresh_configuration_issues(
        self, configured_channels: list[dict[str, Any]] | None = None
    ) -> None:
        """Expose missing channel setup and deleted scripts as repair warnings."""
        configured_channels = configured_channels or self._configured_channels()
        no_channels_issue_id = f"{self.entry.entry_id}_no_delivery_channels"
        missing_script_issue_id = f"{self.entry.entry_id}_missing_delivery_script"
        if not configured_channels:
            async_create_issue(
                self.hass,
                DOMAIN,
                no_channels_issue_id,
                is_fixable=True,
                severity=IssueSeverity.WARNING,
                translation_key="no_delivery_channels",
            )
        else:
            async_delete_issue(self.hass, DOMAIN, no_channels_issue_id)

        if any(
            self.hass.states.get(channel["script_entity_id"]) is None
            for channel in configured_channels
        ):
            async_create_issue(
                self.hass,
                DOMAIN,
                missing_script_issue_id,
                is_fixable=True,
                severity=IssueSeverity.WARNING,
                translation_key="missing_delivery_script",
            )
        else:
            async_delete_issue(self.hass, DOMAIN, missing_script_issue_id)

    async def _async_try_channels(
        self, reminder: Reminder, channels: list[dict[str, Any]]
    ) -> tuple[bool | None, str | None]:
        by_priority: defaultdict[int, list[dict[str, Any]]] = defaultdict(list)
        for channel in channels:
            by_priority[channel["priority"]].append(channel)
        for priority in sorted(by_priority):
            group = by_priority[priority]
            start = self._round_robin[priority] % len(group)
            ordered = group[start:] + group[:start]
            self._round_robin[priority] = start + 1
            for channel in ordered:
                result = await self._async_call_channel(reminder, channel)
                if result is None:
                    return None, None
                if result:
                    return True, channel["id"]
        return False, None

    async def async_test_channel(self, channel_id: str) -> bool:
        """Send one isolated test through a configured channel.

        A test deliberately bypasses reminder state, quiet hours, and fallback
        dispatch. It still shares the selected channel's lock, cooldown,
        timeout, and response validation with regular delivery.
        """
        channel = next(
            (item for item in self.data.get(CONF_CHANNELS, []) if item["id"] == channel_id),
            None,
        )
        state = self.hass.states.get(channel["script_entity_id"]) if channel else None
        if channel is None or self._stopped or state is None or state.state == STATE_UNAVAILABLE:
            return False
        priority = next(
            (
                int(item.get("priority", 1))
                for item in self.data.get(CONF_ASSIGNMENTS, [])
                if item.get("person_entity_id") == self.person_entity_id
                and item.get("channel_id") == channel_id
            ),
            1,
        )
        now = dt_util.utcnow().isoformat()
        payload = {
            "reminder_id": f"test-{uuid4()}",
            "person_entity_id": self.person_entity_id,
            "todo_entity_id": self.todo.entity_id,
            "todo_item_uid": None,
            "title": "HA Reminder channel test",
            "description": "This is a manual notification-channel test.",
            "level": "normal",
            "attempt": 1,
            "channel_priority": priority,
            "created_at": now,
            "due_at": None,
            "is_test": True,
        }
        return await self._async_invoke_channel({**channel, "priority": priority}, payload)

    async def _async_call_channel(
        self, reminder: Reminder, channel: dict[str, Any]
    ) -> bool | None:
        """Call a script with a response, globally serializing that channel."""
        channel_id = channel["id"]
        async with self._channel_locks[channel_id]:
            last = self._channel_last_call.get(channel_id)
            if last:
                delay = CHANNEL_COOLDOWN - (dt_util.utcnow() - last)
                if delay.total_seconds() > 0:
                    _LOGGER.debug("Channel %s queued by cooldown", channel_id)
                    await asyncio.sleep(delay.total_seconds())
            async with self._lock:
                current = self.reminders.get(reminder.item_uid)
                if self._stopped or current is None or current.generation != reminder.generation:
                    return False
                if self._in_quiet_hours(dt_util.now()):
                    return None
            payload = {
                "reminder_id": reminder.reminder_id,
                "person_entity_id": self.person_entity_id,
                "todo_entity_id": self.todo.entity_id,
                "todo_item_uid": reminder.item_uid,
                "title": reminder.title,
                "description": reminder.description,
                "level": "normal",
                "attempt": reminder.delivery_retry_count + 1,
                "channel_priority": channel["priority"],
                "created_at": reminder.created_at,
                "due_at": reminder.due,
            }
            return await self._async_invoke_channel(channel, payload, lock_held=True)

    async def _async_invoke_channel(
        self,
        channel: dict[str, Any],
        payload: dict[str, Any],
        *,
        lock_held: bool = False,
    ) -> bool:
        """Run a channel script and validate its response contract."""
        if lock_held:
            return await self._async_call_channel_script(channel, payload)
        channel_id = channel["id"]
        async with self._channel_locks[channel_id]:
            last = self._channel_last_call.get(channel_id)
            if last:
                delay = CHANNEL_COOLDOWN - (dt_util.utcnow() - last)
                if delay.total_seconds() > 0:
                    _LOGGER.debug("Channel %s queued by cooldown", channel_id)
                    await asyncio.sleep(delay.total_seconds())
            return await self._async_call_channel_script(channel, payload)

    async def _async_call_channel_script(
        self, channel: dict[str, Any], payload: dict[str, Any]
    ) -> bool:
        """Call one script and return whether it explicitly confirmed success."""
        channel_id = channel["id"]
        try:
            self._channel_last_call[channel_id] = dt_util.utcnow()
            response = await asyncio.wait_for(
                self.hass.services.async_call(
                    "script",
                    channel["script_entity_id"].split(".", maxsplit=1)[1],
                    payload,
                    blocking=True,
                    return_response=True,
                ),
                timeout=CHANNEL_TIMEOUT.total_seconds(),
            )
        except (TimeoutError, Exception) as err:  # Script errors are delivery failures.
            _LOGGER.warning(
                "Reminder channel %s failed: %s: %s", channel_id, type(err).__name__, err
            )
            return False
        valid = isinstance(response, dict) and isinstance(response.get("success"), bool)
        if not valid or not response["success"]:
            _LOGGER.warning("Reminder channel %s returned an invalid or failed response", channel_id)
            return False
        return True

    def _in_quiet_hours(self, now: datetime) -> bool:
        start = time.fromisoformat(self.data.get(CONF_QUIET_START, "22:00"))
        end = time.fromisoformat(self.data.get(CONF_QUIET_END, "07:00"))
        current = now.timetz().replace(tzinfo=None)
        return start <= current < end if start < end else current >= start or current < end

    def _quiet_end(self, now: datetime) -> datetime:
        end = time.fromisoformat(self.data.get(CONF_QUIET_END, "07:00"))
        result = now.replace(hour=end.hour, minute=end.minute, second=0, microsecond=0)
        if result <= now:
            result += timedelta(days=1)
        return dt_util.as_utc(result)
