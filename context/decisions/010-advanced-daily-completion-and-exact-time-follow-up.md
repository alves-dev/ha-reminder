# Decision: Advanced Daily Completion and Exact-Time Follow-Up

## Context

An advanced reminder needs a device-visible confirmation that it was completed
today, an explicit choice for persistent alerting after an exact scheduled time,
and a simplified notification-level vocabulary.

## Decision

Persist the local calendar date of the last daily completion with the advanced
reminder's occurrence state. Expose it as a device switch: enabling it completes
the current occurrence or suppresses today's scheduled occurrence; disabling it
removes that suppression. Schedule a midnight state refresh so the switch turns
off automatically.

Use `normal`, `high`, and `critical` as the supported notification levels. Map
legacy `low` values to `normal` at runtime and when configuration is saved.

Add an advanced-form option that controls whether an exact-time occurrence
continues through its normal follow-up cycles. Newly created reminders require
an explicit opt-in; legacy configurations preserve their existing persistent
behavior.

Collect the common reminder definition first, then show a second form with only
the fields applicable to the chosen schedule, time, and completion policy. This
is used instead of attempting reactive field enablement in a Home Assistant
config-flow form.

## Rationale

The completion marker must survive Home Assistant restarts and be scoped to the
local calendar day rather than an arbitrary 24-hour period. Routing the switch
through the existing manager keeps scheduling, persistence, and entity updates
serialized. An explicit exact-time setting makes persistent follow-up visible
at configuration time without silently changing existing reminders.

## Alternatives Considered

- Keep the state only in the switch entity. It would be lost on restart and
  could not prevent a scheduled delivery.
- Add a separate action without a switch. This would not expose the requested
  daily state on the reminder device.
- Remove legacy `low` values without mapping them. Existing configurations
  could then send an unsupported delivery payload.

## Outcomes

The advanced device now has a notification-level sensor and a **Completed
today** switch. The completion marker is cleared by a midnight scheduler wake-up
and legacy `low` values are emitted as `normal`. The exact-time option controls
whether confirmed delivery starts the normal recipient follow-up cycle. The
advanced form now separates common and schedule-specific inputs as of
2026-09-02. If a selection has no applicable detail fields, configuration is
completed directly rather than displaying an empty form.

## Related

- [Feature: Advanced Reminder Devices](../intent/feature-advanced-reminder-devices.md)
- [Decision: Advanced Reminder Runtime Architecture](006-advanced-reminder-runtime-architecture.md)
- [Pattern: Serialized Reminder Scheduling](../knowledge/patterns/serialized-reminder-scheduling.md)
- [Pattern: Manager-Backed Platform Entities](../knowledge/patterns/manager-backed-platform-entities.md)
- [Learning: Local-Day Completion State](../evolution/learning-local-day-completion-state.md)

## Status

- **Created**: 2026-09-01 (Phase: Intent)
- **Status**: Accepted
- **Approval**: User requested implementation on 2026-09-01.
