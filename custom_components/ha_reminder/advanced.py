"""Runtime scheduling and delivery for advanced reminder devices."""

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
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    ADVANCED_STORAGE_KEY,
    AFTERNOON_TIME,
    CHANNEL_COOLDOWN,
    CHANNEL_TIMEOUT,
    COMPLETION_EXPIRE,
    CONF_ASSIGNMENTS,
    CONF_CHANNELS,
    CONF_COMPLETION_POLICY,
    CONF_ENABLED,
    CONF_EXACT_TIME,
    CONF_INTERVAL_DAYS,
    CONF_INTERVALS,
    CONF_LEVEL,
    CONF_MAX_RETRIES,
    CONF_QUIET_END,
    CONF_QUIET_START,
    CONF_RECIPIENTS,
    CONF_RECURRENCE_REFERENCE,
    CONF_RETRY_INTERVAL,
    CONF_SCHEDULE_TYPE,
    CONF_START_DATE,
    CONF_TIME_PERIOD,
    CONF_WEEKDAYS,
    DEFAULT_INTERVALS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_INTERVAL,
    DOMAIN,
    EVENING_TIME,
    LEVEL_NORMAL,
    MORNING_TIME,
    PERIOD_AFTERNOON,
    PERIOD_EVENING,
    PERIOD_EXACT,
    PERIOD_MORNING,
    REFERENCE_COMPLETION,
    SCHEDULE_DAILY,
    SCHEDULE_EVERY_DAYS,
    SCHEDULE_ONCE,
    SCHEDULE_WEEKLY,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)


class AdvancedReminderStore:
    """Persist the state that is separate from advanced reminder configuration."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store = Store[dict[str, Any]](
            hass, STORAGE_VERSION, f"{ADVANCED_STORAGE_KEY}.{entry_id}"
        )
        self.data: dict[str, Any] = {"generation": 0, "active": None, "next_occurrence_at": None}

    async def async_load(self) -> None:
        self.data = await self._store.async_load() or self.data
        self.data.setdefault("generation", 0)
        self.data.setdefault("active", None)
        self.data.setdefault("next_occurrence_at", None)
        self.data.setdefault("last_status", "scheduled")
        self.data.setdefault("configuration", None)

    def async_save(self) -> None:
        self._store.async_delay_save(lambda: self.data, 1)

    async def async_remove(self) -> None:
        await self._store.async_remove()


class AdvancedReminderManager:
    """Own a logical advanced reminder and its shared occurrence lifecycle."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.data = {**entry.data, **entry.options}
        self.store = AdvancedReminderStore(hass, entry.entry_id)
        self._lock = asyncio.Lock()
        self._listeners: list[Callable[[], None]] = []
        self._timer_cancel: CALLBACK_TYPE | None = None
        self._stopped = False
        self._round_robin: defaultdict[str, defaultdict[int, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        dispatcher = hass.data.setdefault(
            DOMAIN, {"channel_locks": defaultdict(asyncio.Lock), "channel_last_call": {}}
        )
        self._channel_locks = dispatcher["channel_locks"]
        self._channel_last_call = dispatcher["channel_last_call"]

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=self.data["title"],
            manufacturer="HA Reminder",
            model="Advanced reminder",
        )

    @property
    def is_enabled(self) -> bool:
        return bool(self.data.get(CONF_ENABLED, True))

    @property
    def status(self) -> str:
        if not self.is_enabled:
            return "disabled"
        if self.store.data["active"]:
            return "active"
        return self.store.data.get("last_status", "scheduled")

    @property
    def next_occurrence_at(self) -> datetime | None:
        value = self.store.data.get("next_occurrence_at")
        return datetime.fromisoformat(value) if value else None

    def async_add_listener(self, listener: Callable[[], None]) -> CALLBACK_TYPE:
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener) if listener in self._listeners else None

    async def async_start(self) -> None:
        """Restore an advanced occurrence and arrange its next wake-up."""
        await self.store.async_load()
        if self.store.data["configuration"] != self._configuration_signature():
            self.store.data["generation"] += 1
            self.store.data["active"] = None
            self.store.data["last_status"] = "scheduled" if self.is_enabled else "disabled"
            following = self._next_schedule(dt_util.now()) if self.is_enabled else None
            self.store.data["next_occurrence_at"] = following.isoformat() if following else None
            self.store.data["configuration"] = self._configuration_signature()
        elif self.is_enabled and not self.store.data["active"] and not self.next_occurrence_at:
            initial = self._next_schedule(dt_util.now(), include_current=True)
            self.store.data["next_occurrence_at"] = initial.isoformat() if initial else None
        self._persist_and_schedule()

    def _configuration_signature(self) -> dict[str, Any]:
        """Return the durable definition whose change invalidates active work."""
        return {
            key: self.data.get(key)
            for key in (
                "title",
                CONF_RECIPIENTS,
                CONF_LEVEL,
                CONF_SCHEDULE_TYPE,
                CONF_START_DATE,
                CONF_TIME_PERIOD,
                CONF_EXACT_TIME,
                CONF_WEEKDAYS,
                CONF_INTERVAL_DAYS,
                CONF_COMPLETION_POLICY,
                CONF_RECURRENCE_REFERENCE,
                CONF_ENABLED,
            )
        }

    async def async_stop(self) -> None:
        self._stopped = True
        if self._timer_cancel:
            self._timer_cancel()
            self._timer_cancel = None

    async def async_complete(self, occurrence_id: str | None = None) -> bool:
        """Complete the current occurrence once; repeated requests are harmless."""
        async with self._lock:
            active = self.store.data["active"]
            if not active or (occurrence_id and occurrence_id != active["occurrence_id"]):
                return False
            completed_at = dt_util.now()
            self.store.data["generation"] += 1
            self.store.data["active"] = None
            self.store.data["last_status"] = "completed"
            scheduled_at = datetime.fromisoformat(active["scheduled_at"])
            reference = (
                completed_at
                if self.data.get(CONF_RECURRENCE_REFERENCE) == REFERENCE_COMPLETION
                else max(scheduled_at, completed_at)
            )
            following = self._next_schedule(reference)
            self.store.data["next_occurrence_at"] = following.isoformat() if following else None
            self._persist_and_schedule()
            return True

    async def async_set_enabled(self, enabled: bool) -> None:
        """Enable future scheduling or cancel the current occurrence permanently."""
        async with self._lock:
            self.data[CONF_ENABLED] = enabled
            self.hass.config_entries.async_update_entry(
                self.entry, options={**self.entry.options, CONF_ENABLED: enabled}
            )
            self.store.data["generation"] += 1
            self.store.data["active"] = None
            if enabled:
                following = self._next_schedule(dt_util.now())
                self.store.data["next_occurrence_at"] = following.isoformat() if following else None
                self.store.data["last_status"] = "scheduled"
            else:
                self.store.data["next_occurrence_at"] = None
                self.store.data["last_status"] = "disabled"
            self.store.data["configuration"] = self._configuration_signature()
            self._persist_and_schedule()

    def _period_time(self) -> time:
        period = self.data.get(CONF_TIME_PERIOD, PERIOD_EXACT)
        raw = {
            PERIOD_MORNING: MORNING_TIME,
            PERIOD_AFTERNOON: AFTERNOON_TIME,
            PERIOD_EVENING: EVENING_TIME,
        }.get(period, self.data.get(CONF_EXACT_TIME, MORNING_TIME))
        return time.fromisoformat(raw)

    def _next_schedule(self, reference: datetime, *, include_current: bool = False) -> datetime | None:
        """Resolve the configured schedule to the next local execution time."""
        start = date.fromisoformat(self.data[CONF_START_DATE])
        local_reference = dt_util.as_local(reference)
        candidate_time = self._period_time()
        schedule_type = self.data[CONF_SCHEDULE_TYPE]

        def as_utc(candidate_date: date) -> datetime:
            return dt_util.as_utc(dt_util.as_local(datetime.combine(candidate_date, candidate_time)))

        def eligible(candidate: datetime) -> bool:
            return candidate >= reference if include_current else candidate > reference

        if schedule_type == SCHEDULE_ONCE:
            candidate = as_utc(start)
            return candidate if eligible(candidate) else None
        if schedule_type == SCHEDULE_EVERY_DAYS:
            interval = int(self.data.get(CONF_INTERVAL_DAYS, 1))
            if (
                self.data.get(CONF_RECURRENCE_REFERENCE) == REFERENCE_COMPLETION
                and not include_current
            ):
                return as_utc(local_reference.date() + timedelta(days=interval))
            days = max(0, (local_reference.date() - start).days)
            offset = ((days + interval - 1) // interval) * interval
            candidate = as_utc(start + timedelta(days=offset))
            if not eligible(candidate):
                candidate = as_utc(start + timedelta(days=offset + interval))
            return candidate

        weekdays = [int(day) for day in self.data.get(CONF_WEEKDAYS, [])]
        if schedule_type == SCHEDULE_WEEKLY and not weekdays:
            weekdays = [start.weekday()]
        if schedule_type == SCHEDULE_DAILY:
            weekdays = list(range(7))
        for offset in range(0, 8):
            candidate_date = max(start, local_reference.date()) + timedelta(days=offset)
            if candidate_date.weekday() not in weekdays:
                continue
            candidate = as_utc(candidate_date)
            if eligible(candidate):
                return candidate
        return None

    def _next_wakeup(self) -> datetime | None:
        candidates: list[datetime] = []
        if self.is_enabled and not self.store.data["active"] and self.next_occurrence_at:
            candidates.append(self.next_occurrence_at)
        active = self.store.data["active"]
        if active:
            if self.data.get(CONF_COMPLETION_POLICY) == COMPLETION_EXPIRE:
                scheduled = dt_util.as_local(datetime.fromisoformat(active["scheduled_at"]))
                end = scheduled.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                candidates.append(dt_util.as_utc(end))
            candidates.extend(datetime.fromisoformat(item["next_at"]) for item in active["recipients"].values())
        return min(candidates, default=None)

    def _persist_and_schedule(self) -> None:
        self.store.async_save()
        self._schedule_next()
        for listener in list(self._listeners):
            listener()

    def _schedule_next(self) -> None:
        if self._timer_cancel:
            self._timer_cancel()
            self._timer_cancel = None
        if when := self._next_wakeup():
            self._timer_cancel = async_track_point_in_utc_time(
                self.hass, self._async_timer, max(when, dt_util.utcnow())
            )

    async def _async_timer(self, _now: datetime) -> None:
        async with self._lock:
            self._timer_cancel = None
            await self._async_advance_occurrence_locked()
            active = self.store.data["active"]
            due = []
            if active:
                due = [
                    person
                    for person, state in active["recipients"].items()
                    if datetime.fromisoformat(state["next_at"]) <= dt_util.utcnow()
                ]
                generation = active["generation"]
            else:
                generation = 0
        await asyncio.gather(*(self._async_deliver(person, generation) for person in due))
        async with self._lock:
            self._schedule_next()

    async def _async_advance_occurrence_locked(self) -> None:
        if self._stopped or not self.is_enabled:
            return
        active = self.store.data["active"]
        if active and self.data.get(CONF_COMPLETION_POLICY) == COMPLETION_EXPIRE:
            scheduled = dt_util.as_local(datetime.fromisoformat(active["scheduled_at"]))
            if dt_util.now().date() > scheduled.date():
                self.store.data["generation"] += 1
                self.store.data["active"] = None
                self.store.data["last_status"] = "expired"
                next_at = self._next_schedule(datetime.fromisoformat(active["scheduled_at"]))
                self.store.data["next_occurrence_at"] = next_at.isoformat() if next_at else None
                active = None
        if active or not self.next_occurrence_at or self.next_occurrence_at > dt_util.utcnow():
            return
        self.store.data["generation"] += 1
        generation = self.store.data["generation"]
        scheduled_at = self.next_occurrence_at
        self.store.data["active"] = {
            "occurrence_id": str(uuid4()),
            "generation": generation,
            "scheduled_at": scheduled_at.isoformat(),
            "recipients": {
                person: {"next_at": scheduled_at.isoformat(), "cycle": 0, "retries": 0}
                for person in self.data[CONF_RECIPIENTS]
            },
        }
        self.store.data["last_status"] = "active"
        next_at = self._next_schedule(scheduled_at)
        self.store.data["next_occurrence_at"] = next_at.isoformat() if next_at else None
        self.store.async_save()

    def _person_data(self, person_entity_id: str) -> dict[str, Any] | None:
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            entry_data = {**entry.data, **entry.options}
            if entry_data.get("person_entity_id") == person_entity_id:
                return entry_data
        return None

    @staticmethod
    def _configured_channels(person: str, data: dict[str, Any]) -> list[dict[str, Any]]:
        channels = {item["id"]: item for item in data.get(CONF_CHANNELS, []) if item.get("enabled", True)}
        return [
            {**channels[assignment["channel_id"]], "priority": int(assignment.get("priority", 1))}
            for assignment in data.get(CONF_ASSIGNMENTS, [])
            if assignment.get("person_entity_id") == person and assignment.get("channel_id") in channels
        ]

    async def _async_deliver(self, person: str, generation: int) -> None:
        async with self._lock:
            active = self.store.data["active"]
            if self._stopped or not active or active["generation"] != generation:
                return
            recipient = active["recipients"].get(person)
            if not recipient:
                return
            data = self._person_data(person)
            if not data:
                return
            if self.data.get(CONF_LEVEL) in ("low", LEVEL_NORMAL) and self._in_quiet_hours(data):
                recipient["next_at"] = self._quiet_end(data).isoformat()
                self._persist_and_schedule()
                return
            configured = self._configured_channels(person, data)
            if not configured:
                recipient["next_at"] = (dt_util.utcnow() + timedelta(minutes=5)).isoformat()
                self._persist_and_schedule()
                return
            channels = [
                channel
                for channel in configured
                if (state := self.hass.states.get(channel["script_entity_id"])) is not None
                and state.state != STATE_UNAVAILABLE
            ]
        result, channel_id = await self._async_try_channels(person, data, generation, channels)
        async with self._lock:
            active = self.store.data["active"]
            if self._stopped or not active or active["generation"] != generation:
                return
            recipient = active["recipients"].get(person)
            if not recipient:
                return
            if result is None:
                recipient["next_at"] = self._quiet_end(data).isoformat()
            elif result:
                recipient["cycle"] += 1
                recipient["retries"] = 0
                intervals = data.get(CONF_INTERVALS, DEFAULT_INTERVALS)
                delay = intervals[min(recipient["cycle"], len(intervals) - 1)]
                recipient["next_at"] = (dt_util.utcnow() + timedelta(seconds=delay)).isoformat()
            else:
                recipient["retries"] += 1
                if recipient["retries"] <= data.get(CONF_MAX_RETRIES, DEFAULT_MAX_RETRIES):
                    delay = data.get(CONF_RETRY_INTERVAL, DEFAULT_RETRY_INTERVAL)
                else:
                    recipient["retries"] = 0
                    delay = data.get(CONF_INTERVALS, DEFAULT_INTERVALS)[0]
                recipient["next_at"] = (dt_util.utcnow() + timedelta(seconds=delay)).isoformat()
            self._persist_and_schedule()

    async def _async_try_channels(
        self, person: str, data: dict[str, Any], generation: int, channels: list[dict[str, Any]]
    ) -> tuple[bool | None, str | None]:
        grouped: defaultdict[int, list[dict[str, Any]]] = defaultdict(list)
        for channel in channels:
            grouped[channel["priority"]].append(channel)
        for priority in sorted(grouped):
            group = grouped[priority]
            start = self._round_robin[person][priority] % len(group)
            ordered = group[start:] + group[:start]
            self._round_robin[person][priority] = start + 1
            for channel in ordered:
                result = await self._async_call_channel(person, data, generation, channel)
                if result is None:
                    return None, None
                if result:
                    return True, channel["id"]
        return False, None

    async def _async_call_channel(
        self, person: str, data: dict[str, Any], generation: int, channel: dict[str, Any]
    ) -> bool | None:
        channel_id = channel["id"]
        async with self._channel_locks[channel_id]:
            last = self._channel_last_call.get(channel_id)
            if last and (delay := CHANNEL_COOLDOWN - (dt_util.utcnow() - last)).total_seconds() > 0:
                await asyncio.sleep(delay.total_seconds())
            async with self._lock:
                active = self.store.data["active"]
                if self._stopped or not active or active["generation"] != generation:
                    return False
                if self.data.get(CONF_LEVEL) in ("low", LEVEL_NORMAL) and self._in_quiet_hours(data):
                    return None
                recipient = active["recipients"][person]
                payload = {
                    "reminder_id": active["occurrence_id"],
                    "person_entity_id": person,
                    "todo_entity_id": None,
                    "todo_item_uid": None,
                    "title": self.data["title"],
                    "description": None,
                    "level": self.data.get(CONF_LEVEL, "low"),
                    "attempt": recipient["retries"] + 1,
                    "channel_priority": channel["priority"],
                    "created_at": active["scheduled_at"],
                    "due_at": active["scheduled_at"],
                }
            try:
                self._channel_last_call[channel_id] = dt_util.utcnow()
                response = await asyncio.wait_for(
                    self.hass.services.async_call(
                        "script", "turn_on", {"entity_id": channel["script_entity_id"], "variables": payload},
                        blocking=True, return_response=True,
                    ), timeout=CHANNEL_TIMEOUT.total_seconds(),
                )
            except Exception as err:  # timeout and script exceptions are channel failures
                _LOGGER.warning("Advanced reminder channel %s failed: %s", channel_id, type(err).__name__)
                return False
            return isinstance(response, dict) and isinstance(response.get("success"), bool) and response["success"]

    @staticmethod
    def _in_quiet_hours(data: dict[str, Any]) -> bool:
        start = time.fromisoformat(data.get(CONF_QUIET_START, "22:00"))
        end = time.fromisoformat(data.get(CONF_QUIET_END, "07:00"))
        now = dt_util.now().timetz().replace(tzinfo=None)
        return start <= now < end if start < end else now >= start or now < end

    @staticmethod
    def _quiet_end(data: dict[str, Any]) -> datetime:
        end = time.fromisoformat(data.get(CONF_QUIET_END, "07:00"))
        result = dt_util.now().replace(hour=end.hour, minute=end.minute, second=0, microsecond=0)
        if result <= dt_util.now():
            result += timedelta(days=1)
        return dt_util.as_utc(result)
