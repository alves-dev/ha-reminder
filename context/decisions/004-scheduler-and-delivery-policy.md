# Decision: Scheduler and Delivery Policy

## Context

The integration must schedule many independent reminders without duplicate work,
avoid notifications during quiet hours, and distinguish a failed delivery from a
successful reminder cycle.

## Decision

Maintain one next-due timer per person-scoped manager, serialize state mutation
with an asynchronous lock, and deliver due items concurrently outside that lock.
Use progressive intervals after success; use a bounded retry count and retry
interval after failure; defer low-priority reminders to the end of quiet hours.
Interpret a date-only due value using 09:00 in local time, then persist times as
UTC ISO timestamps.

## Rationale

This behavior is encoded in the manager constants and scheduling methods. It
minimizes active timers while retaining independent reminder records, keeps
state transitions safe across asynchronous delivery, and gives date-only tasks a
predictable time. The code and architecture documentation establish the policy;
the original selection rationale is otherwise inferred.

## Alternatives Considered

Alternatives are not documented in the existing codebase. Alternatives include a
timer per reminder, advancing the schedule during quiet hours, retrying forever,
or treating date-only items as midnight; none is selected.

## Outcomes

After a successful initial delivery, the scheduler advances to the next progressive interval. A
missing channel setup is a configuration-incomplete state; configured scripts that are unavailable
remain a normal complete-delivery failure and use the retry policy.

## Related

- [Project Intent](../intent/project-intent.md)
- [Feature: Persistent Follow-Up Scheduling](../intent/feature-persistent-follow-up.md)
- [Feature: Configurable Delivery Fallback](../intent/feature-delivery-fallback.md)
- [Feature: Advanced Reminder Devices](../intent/feature-advanced-reminder-devices.md)
- [Decision: Persistent Reminder Lifecycle](003-persistent-reminder-lifecycle.md)
- [Decision: Script-Based Delivery Channels](005-script-based-delivery-channels.md)

## Status

- **Created**: 2026-08-30 (Phase: Intent)
- **Status**: Accepted
- **Note**: Documented from existing implementation.
