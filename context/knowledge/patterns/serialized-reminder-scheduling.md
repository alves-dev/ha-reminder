# Pattern: Serialized Reminder Scheduling

## Description

Use a single reschedulable timer for the earliest reminder, protect shared state
with an asynchronous lock, and execute due deliveries outside the critical
section.

## When to Use

Use this for a person-scoped collection of independently due tasks where state
changes can arrive concurrently with timer callbacks or delivery results.

## Pattern

Cancel the prior timer before scheduling the next earliest due time. Under the
lock, collect eligible work and clear the active timer. Run delivery coroutines
concurrently, then reacquire the lock to schedule the next timer.

## Example

```python
def _schedule_next(self) -> None:
    if self._timer_cancel:
        self._timer_cancel()
    next_item = self.next_reminder
    if next_item:
        when = max(next_item.next_at, dt_util.utcnow())
        self._timer_cancel = async_track_point_in_utc_time(
            self.hass, self._async_timer, when
        )

async def _async_timer(self, _now: datetime) -> None:
    async with self._lock:
        self._timer_cancel = None
        due = [item for item in self.reminders.values() if item.next_at <= dt_util.utcnow()]
    await asyncio.gather(*(self._async_deliver(item.item_uid, item.generation) for item in due))
    async with self._lock:
        self._schedule_next()
```

## Files Using This Pattern

- `custom_components/ha_reminder/manager.py` — schedules and dispatches reminder cycles.

## Related

- [Decision: Scheduler and Delivery Policy](../../decisions/004-scheduler-and-delivery-policy.md)
- [Feature: Persistent Follow-Up Scheduling](../../intent/feature-persistent-follow-up.md)

## Status

- **Created**: 2026-08-30
- **Status**: Active
