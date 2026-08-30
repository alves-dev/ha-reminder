# Feature: Per-Person Reminder Lists

## What

Each configured person receives a dedicated reminder list. Every outstanding
item in that list is treated as an individual reminder, and completing or
deleting it stops future follow-up.

## Why

People need ownership of their own tasks. Separate lists make responsibility
clear while giving each person a simple, familiar place to add and complete
reminders.

## Acceptance Criteria

- [x] A configured person has a dedicated reminder list.
- [x] A pending list item becomes an independently managed reminder.
- [x] Completing or deleting an item prevents further reminders for it.
- [x] Editing an outstanding item restarts its reminder follow-up.

## Related

- [Project Intent](project-intent.md)
- [Decision: Home Assistant Integration Architecture](../decisions/002-home-assistant-integration-architecture.md)
- [Decision: Persistent Reminder Lifecycle](../decisions/003-persistent-reminder-lifecycle.md)
- [Pattern: Local To-Do Item Lifecycle](../knowledge/patterns/local-todo-item-lifecycle.md)

## Status

- **Created**: 2026-08-30 (Phase: Intent)
- **Status**: Active (already implemented)
