# Pattern: Priority Fallback Channel Dispatch

## Description

Dispatch through a prioritized set of delivery routes, rotate equal-priority
routes, and fail over when a route does not explicitly report success.

## When to Use

Use this when a message can reach its recipient through several interchangeable
routes and each route can provide a success or failure response.

## Pattern

Group routes by priority, process groups from lowest number upward, rotate the
starting route within each group, and stop at the first successful response. For
shared routes, serialize invocations and enforce a cooldown before making the
call.

## Example

```python
for priority in sorted(by_priority):
    group = by_priority[priority]
    start = self._round_robin[priority] % len(group)
    ordered = group[start:] + group[:start]
    self._round_robin[priority] = start + 1
    for channel in ordered:
        if await self._async_call_channel(reminder, channel):
            return True, channel["id"]
return False, None
```

## Files Using This Pattern

- `custom_components/ha_reminder/manager.py` — selects routes, checks responses, and enforces shared-route cooldown.
- `custom_components/ha_reminder/config_flow.py` — stores per-person route assignments and priorities.

## Related

- [Decision: Script-Based Delivery Channels](../../decisions/005-script-based-delivery-channels.md)
- [Decision: Scheduler and Delivery Policy](../../decisions/004-scheduler-and-delivery-policy.md)
- [Feature: Configurable Delivery Fallback](../../intent/feature-delivery-fallback.md)

## Status

- **Created**: 2026-08-30
- **Status**: Active
