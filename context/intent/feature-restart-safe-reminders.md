# Feature: Restart-Safe Reminders

## What

Reminder items and their follow-up state survive a service restart. When the
service returns, outstanding items are reconciled so that completed, removed,
or changed items have the correct future behavior.

## Why

Reminder follow-up must remain dependable through routine upgrades, reloads, and
unexpected interruptions. Users should not need to recreate tasks after a
restart or receive obsolete reminders.

## Acceptance Criteria

- [x] Outstanding reminder state is retained across restarts.
- [x] Outstanding list items are restored after startup.
- [x] Removed and completed items are no longer scheduled.
- [x] Changes invalidate earlier pending work for the same item.

## Related

- [Project Intent](project-intent.md)
- [Decision: Persistent Reminder Lifecycle](../decisions/003-persistent-reminder-lifecycle.md)
- [Pattern: Reminder Generation Reconciliation](../knowledge/patterns/reminder-generation-reconciliation.md)

## Status

- **Created**: 2026-08-30 (Phase: Intent)
- **Status**: Active (already implemented)
