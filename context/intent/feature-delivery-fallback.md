# Feature: Configurable Delivery Fallback

## What

Users can configure and prioritize delivery routes for each person. A reminder
tries the preferred route first and continues to alternatives when delivery is
not confirmed, with fair rotation among equally preferred routes.

## Why

The best way to reach someone varies by situation. Fallback prevents one
unavailable surface from silently ending follow-up and lets households use the
notification destinations they already rely on.

## Acceptance Criteria

- [x] Users can add, update, enable, and remove delivery routes for a person.
- [x] Delivery attempts honor the configured preference order.
- [x] A failed or unconfirmed attempt moves on to an alternative route.
- [x] Equally preferred routes rotate across attempts.
- [x] A route is not invoked too frequently when shared.
- [x] Users can create a ready-to-configure script channel that delivers to one
  selected notification target.

## Related

- [Project Intent](project-intent.md)
- [Decision: Script-Based Delivery Channels](../decisions/005-script-based-delivery-channels.md)
- [Blueprint: Notification Channel](../../blueprints/script/ha_reminder/notification_channel.yaml)
- [Feature: Delivery Channel Testing](feature-delivery-channel-testing.md)
- [Decision: Scheduler and Delivery Policy](../decisions/004-scheduler-and-delivery-policy.md)
- [Pattern: Priority Fallback Channel Dispatch](../knowledge/patterns/priority-fallback-channel-dispatch.md)

## Status

- **Created**: 2026-08-30 (Phase: Intent)
- **Status**: Active
