# Feature: Persistent Follow-Up Scheduling

## What

Outstanding reminders are delivered repeatedly over time. Users can set a
progressive follow-up schedule, due dates, quiet hours, and a retry policy for
unsuccessful delivery attempts.

## Why

Important tasks should remain visible until they are resolved without creating
unwanted disturbance during a person's quiet hours. Flexible timing lets each
person balance persistence with convenience.

## Acceptance Criteria

- [x] A reminder is first scheduled from its due time or configured follow-up timing.
- [x] Follow-up continues after successful delivery while the item remains outstanding.
- [x] Unsuccessful delivery is retried according to the configured policy.
- [x] Reminders that fall in quiet hours are deferred.
- [x] Date-only due items use a consistent morning reference.

## Related

- [Project Intent](project-intent.md)
- [Decision: Persistent Reminder Lifecycle](../decisions/003-persistent-reminder-lifecycle.md)
- [Decision: Scheduler and Delivery Policy](../decisions/004-scheduler-and-delivery-policy.md)
- [Pattern: Serialized Reminder Scheduling](../knowledge/patterns/serialized-reminder-scheduling.md)

## Status

- **Created**: 2026-08-30 (Phase: Intent)
- **Status**: Active (already implemented)
