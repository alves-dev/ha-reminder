# Feature: Advanced Reminder Devices

## What

Users can create a named reminder as its own Home Assistant device. A reminder
can target one or more configured people, repeat on a schedule, remain active
until it is completed or expire at the end of its scheduled day.

## Why

Some household obligations are not naturally represented as a single item in a
person's list. A dedicated device makes recurring, shared and higher-priority
reminders visible and controllable without weakening the simple list workflow.

## Acceptance Criteria

- [x] Users can create and edit an advanced reminder from the integration UI.
- [x] An advanced reminder has an enable switch plus status and next-occurrence
  visibility.
- [x] One occurrence delivers independently to every selected person using
  that person's existing delivery policy.
- [x] One-time and recurring schedules resolve to a concrete local time.
- [x] Completion is available through a generic idempotent integration action.
- [x] Completion, expiration, disablement, editing and restart cancel stale
  delivery work safely.

## Related

- [Project Intent](project-intent.md)
- [Decision: Advanced Reminder Runtime Architecture](../decisions/006-advanced-reminder-runtime-architecture.md)
- [Decision: Scheduler and Delivery Policy](../decisions/004-scheduler-and-delivery-policy.md)
- [Decision: Script-Based Delivery Channels](../decisions/005-script-based-delivery-channels.md)
- [Pattern: Serialized Reminder Scheduling](../knowledge/patterns/serialized-reminder-scheduling.md)
- [Pattern: Reminder Generation Reconciliation](../knowledge/patterns/reminder-generation-reconciliation.md)

## Status

- **Created**: 2026-08-30 (Phase: Intent)
- **Status**: Active (implemented)
- **Approval**: User requested implementation on 2026-08-30.
