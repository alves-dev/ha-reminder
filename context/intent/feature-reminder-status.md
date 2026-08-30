# Feature: Reminder Status Visibility

## What

Each person's reminder setup exposes the current number of outstanding reminders
and the next scheduled reminder, including identifying information for the next
item when one exists.

## Why

Users and household automations need a quick way to see whether reminders are
waiting and when the next follow-up is expected.

## Acceptance Criteria

- [x] The outstanding reminder count is visible per person.
- [x] The next scheduled reminder is visible when one exists.
- [x] The next reminder includes enough information to identify the related item.
- [x] Status updates when reminder state changes.

## Related

- [Project Intent](project-intent.md)
- [Decision: Home Assistant Integration Architecture](../decisions/002-home-assistant-integration-architecture.md)
- [Pattern: Manager-Backed Platform Entities](../knowledge/patterns/manager-backed-platform-entities.md)

## Status

- **Created**: 2026-08-30 (Phase: Intent)
- **Status**: Active (already implemented)
