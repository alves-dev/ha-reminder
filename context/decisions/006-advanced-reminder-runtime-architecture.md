# Decision: Advanced Reminder Runtime Architecture

## Context

Advanced reminders have a device-level lifecycle, potentially target several
people, and require recipient-specific delivery state while retaining one shared
completion outcome.

## Decision

Represent each advanced reminder as its own config entry and logical Home
Assistant device. Its manager persists one occurrence and recipient state per
active reminder, while reading recipient delivery configuration from the
existing person entries. Expose a switch and status sensors on the reminder
device, and route completion through one integration action.

## Rationale

An independent config entry makes the reminder device removable, editable and
reloadable without coupling it to one recipient. Keeping recipient delivery
state inside the occurrence lets all recipients follow their own quiet hours,
channels and retry policy while a completion atomically ends the shared work.

## Alternatives Considered

- Attach an advanced reminder to one person's existing entry. This would make
  shared ownership and removal ambiguous.
- Create an entity for each occurrence. This would expose ephemeral runtime
  work as persistent user configuration.
- Duplicate a reminder for every recipient. This would not support a shared,
  idempotent completion action.

## Outcomes

The implementation uses a persisted occurrence generation and recipient map.
Advanced entries reload after edits, invalidating an active occurrence before the
new definition calculates its next future schedule. The generic interaction
service routes completion by advanced config-entry identifier.

## Related

- [Project Intent](../intent/project-intent.md)
- [Feature: Advanced Reminder Devices](../intent/feature-advanced-reminder-devices.md)
- [Decision: Home Assistant Integration Architecture](002-home-assistant-integration-architecture.md)
- [Decision: Scheduler and Delivery Policy](004-scheduler-and-delivery-policy.md)
- [Decision: Script-Based Delivery Channels](005-script-based-delivery-channels.md)

## Status

- **Created**: 2026-08-30 (Phase: Intent)
- **Status**: Accepted
- **Approval**: User requested implementation on 2026-08-30.
