# Learning: A Script Blueprint Can Be a Typed Delivery Adapter

## Insight

A Home Assistant script blueprint can turn a generic integration payload into a
configured external action while preserving a typed response boundary. Its
inputs configure the destination once; the script variables carry each delivery
request; and a `stop` action returns the result mapping to the caller.

## Evidence

The notification-channel blueprint selects a `notify` entity, renders ordinary
and test deliveries differently, then returns `success: true` through
`response_variable`. The caller invokes the script's named service, rather than
the asynchronous `script.turn_on` action, so HA Reminder receives that response
without needing to know which notification provider receives the message.

## Reuse

Use this adapter shape for other reusable channels, including announcements and
webhooks: expose only destination-specific inputs, consume the common request
payload, and return a documented mapping from the script.

## Related

- [Feature: Configurable Delivery Fallback](../intent/feature-delivery-fallback.md)
- [Decision: Script-Based Delivery Channels](../decisions/005-script-based-delivery-channels.md)
- [Blueprint: Notification Channel](../../blueprints/script/ha_reminder/notification_channel.yaml)

## Status

- **Created**: 2026-08-31 (Phase: Learn)
- **Status**: Active
