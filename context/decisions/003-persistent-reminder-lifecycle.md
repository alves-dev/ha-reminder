# Decision: Persistent Reminder Lifecycle

## Context

Reminder follow-up must survive reloads and restarts while avoiding delivery of
stale work after a task is edited, completed, or deleted.

## Decision

Persist the local task data and one serializable reminder record per pending
item. On startup and every task-list change, reconcile pending items with saved
records. Assign each record a generation number and require asynchronous delivery
work to match the current generation before updating state.

## Rationale

The code stores reminder and task-list data in Home Assistant's versioned local
storage and reconstructs the runtime state at startup. The generation check
invalidates an already-running attempt when an item changes, preventing a late
result from rescheduling obsolete content. Rationale is inferred from the
reconciliation and delivery code.

## Alternatives Considered

Alternatives are not documented in the existing codebase. They include retaining
state only in memory, storing a separate persistent job for every attempt, or
allowing in-flight work to update changed items; none is implemented.

## Outcomes

Outcomes to be documented as the project evolves.

## Related

- [Project Intent](../intent/project-intent.md)
- [Feature: Per-Person Reminder Lists](../intent/feature-per-person-reminder-lists.md)
- [Feature: Persistent Follow-Up Scheduling](../intent/feature-persistent-follow-up.md)
- [Feature: Restart-Safe Reminders](../intent/feature-restart-safe-reminders.md)
- [Decision: Scheduler and Delivery Policy](004-scheduler-and-delivery-policy.md)

## Status

- **Created**: 2026-08-30 (Phase: Intent)
- **Status**: Accepted
- **Note**: Documented from existing implementation.
