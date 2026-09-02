# Feature: Delivery Channel Testing

## What

Users can send a direct test through one configured notification channel from
that person's reminder settings and see whether the channel confirms delivery.

## Why

Channel scripts are customizable and can depend on devices, services, and
household automations. A direct test lets a user validate a channel at setup
time without waiting for a reminder or changing any outstanding reminder.

## Acceptance Criteria

- [x] A user can select a configured notification channel from person settings.
- [x] The selected channel receives a test using the documented channel
  contract and can identify it as a test.
- [x] The settings flow clearly reports whether the script confirmed success.
- [x] A test neither creates nor changes a reminder, its schedule, or fallback
  behavior.
- [x] A failed, unavailable, timed-out, or invalid script response is reported
  as an unsuccessful test.

## Related

- [Project Intent](project-intent.md)
- [Feature: Configurable Delivery Fallback](feature-delivery-fallback.md)
- [Feature: Reminder Configuration](feature-reminder-configuration.md)
- [Decision: Home Assistant Integration Architecture](../decisions/002-home-assistant-integration-architecture.md)
- [Decision: Script-Based Delivery Channels](../decisions/005-script-based-delivery-channels.md)
- [Decision: Isolated Delivery Channel Tests](../decisions/007-isolated-delivery-channel-tests.md)
- [Pattern: Priority Fallback Channel Dispatch](../knowledge/patterns/priority-fallback-channel-dispatch.md)

## Status

- **Created**: 2026-08-30 (Phase: Intent)
- **Status**: Active (implemented)
