# Feature: Reminder Configuration

## What

Users can select the person whose reminders they want to manage and adjust that
person's follow-up timing, quiet hours, retry behavior, and delivery routes.

## Why

Reminder timing and preferred destinations are personal. Guided configuration
lets users tailor follow-up without changing the task workflow itself.

## Acceptance Criteria

- [x] A user can select a person to configure.
- [x] A person cannot be configured more than once.
- [x] Users can change follow-up and quiet-hour settings.
- [x] Users receive validation feedback for invalid timing intervals.
- [x] Users can manage delivery-route assignments.

## Related

- [Project Intent](project-intent.md)
- [Decision: Home Assistant Integration Architecture](../decisions/002-home-assistant-integration-architecture.md)
- [Pattern: Configuration Normalization and Validation](../knowledge/patterns/configuration-normalization-and-validation.md)
- [Feature: Delivery Channel Testing](feature-delivery-channel-testing.md)

## Status

- **Created**: 2026-08-30 (Phase: Intent)
- **Status**: Active (already implemented)
