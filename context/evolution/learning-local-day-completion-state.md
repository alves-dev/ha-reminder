# Learning: Local-Day Completion State

## Observation

A reminder's "completed today" state is a calendar-day outcome, not a duration
from the moment a user toggles a switch.

## Reusable Insight

Persist the local date of completion and schedule the next local midnight as a
state refresh. Derive the switch state by comparing that value with the current
local date. This survives restarts, avoids time-zone-sensitive 24-hour timers,
and lets the scheduler suppress an occurrence before it is delivered.

## Related

- [Decision: Advanced Daily Completion and Exact-Time Follow-Up](../decisions/010-advanced-daily-completion-and-exact-time-follow-up.md)
- [Feature: Advanced Reminder Devices](../intent/feature-advanced-reminder-devices.md)
- [Pattern: Serialized Reminder Scheduling](../knowledge/patterns/serialized-reminder-scheduling.md)

## Status

- **Created**: 2026-09-01 (Phase: Learn)
- **Status**: Active
