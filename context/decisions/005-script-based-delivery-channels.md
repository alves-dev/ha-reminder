# Decision: Script-Based Delivery Channels

## Context

Reminder delivery must work with varied household surfaces without embedding
knowledge of specific phones, speakers, displays, or notification providers in
the integration.

## Decision

Represent every delivery channel as a reusable Home Assistant script. Assign
channels to people with per-person priority. Invoke scripts with a stable
reminder payload and require a mapping with a boolean `success` response. Group
channels by priority, rotate equal-priority channels, try lower-priority groups
after failures, limit each call to five seconds, and globally serialize calls to
a shared channel with a five-second cooldown.

Call the script's own service name, derived from its `script.*` entity ID, when
waiting for the response. Do not call `script.turn_on`: that action starts work
in the background and cannot return the script's response mapping.

Provide a script blueprint for the standard case of sending to a selected
`notify` entity. The blueprint renders the reminder payload, marks manual
tests, and returns `success: true` only after Home Assistant accepts the notify
action.

## Rationale

The script contract separates delivery presentation from reminder state and
allows household automations to choose destinations. Response-based fallback
prevents an invocation from being treated as delivery without confirmation.
Shared-channel locking and cooldown protect a shared destination from concurrent
bursts. Rationale is documented in the architecture file and inferred from the
dispatcher implementation.

## Alternatives Considered

Alternatives are not documented in the existing codebase. Alternatives include
direct calls to individual notification services, a fixed single destination,
or accepting fire-and-forget delivery without a result; none is selected.

## Outcomes

Manual channel tests invoke only the selected script with the normal response
contract plus an `is_test` flag. They share invocation safeguards but do not
enter the reminder scheduling or fallback lifecycle.

The bundled script blueprint selects one notify entity, displays a distinct
manual-test notification, and returns the required boolean response after Home
Assistant accepts the notification action. YAML parsing, the full unit suite,
lint, compilation, and integration-structure validation pass.

Both person and advanced dispatchers call the response-capable named script
service rather than `script.turn_on`, so the channel contract is received by
the integration.

## Related

- [Project Intent](../intent/project-intent.md)
- [Feature: Configurable Delivery Fallback](../intent/feature-delivery-fallback.md)
- [Feature: Persistent Follow-Up Scheduling](../intent/feature-persistent-follow-up.md)
- [Feature: Advanced Reminder Devices](../intent/feature-advanced-reminder-devices.md)
- [Feature: Delivery Channel Testing](../intent/feature-delivery-channel-testing.md)
- [Decision: Scheduler and Delivery Policy](004-scheduler-and-delivery-policy.md)
- [Decision: Isolated Delivery Channel Tests](007-isolated-delivery-channel-tests.md)
- [Blueprint: Notification Channel](../../blueprints/script/ha_reminder/notification_channel.yaml)

## Status

- **Created**: 2026-08-30 (Phase: Intent)
- **Status**: Accepted
- **Note**: Documented from existing implementation.
