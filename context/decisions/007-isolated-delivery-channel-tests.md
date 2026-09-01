# Decision: Isolated Delivery Channel Tests

## Context

Users need a quick way to validate one configured delivery script. Normal
reminder delivery owns reminder state, observes quiet hours, and uses priority
fallback; using it for a manual test would mutate scheduling state and could
send through an unintended channel.

## Decision

Expose a person-settings action that calls exactly the selected configured
script with the existing delivery contract plus `is_test: true`. The test uses
the same per-channel lock, five-second cooldown, five-second timeout, and
boolean `success` response validation as normal delivery. It does not inspect
quiet hours, create reminder state, change delivery history, or invoke fallback
channels.

## Rationale

Calling the actual script verifies the integration boundary that users need to
trust while preserving the isolation of a manual configuration action. Reusing
the call safeguards prevents a test from competing unsafely with a reminder on
a shared channel.

## Alternatives Considered

- Send a synthetic reminder through normal fallback dispatch: rejected because
  it can mutate reminder policy and test a different channel after failure.
- Validate only that the script entity exists: rejected because it cannot prove
  the script's notification behavior or response contract.
- Ignore cooldown and locking for manual tests: rejected because it can burst a
  shared destination while normal delivery is active.

## Outcomes

The options flow reports the selected script's explicit confirmation or failure
in its description, rather than through a translated base error.
Focused unit tests verify the isolated test payload, an unavailable script, and
an invalid response; lint, compilation, and integration-structure validation
also pass.

## Related

- [Project Intent](../intent/project-intent.md)
- [Feature: Delivery Channel Testing](../intent/feature-delivery-channel-testing.md)
- [Feature: Configurable Delivery Fallback](../intent/feature-delivery-fallback.md)
- [Feature: Reminder Configuration](../intent/feature-reminder-configuration.md)
- [Decision: Script-Based Delivery Channels](005-script-based-delivery-channels.md)
- [Pattern: Priority Fallback Channel Dispatch](../knowledge/patterns/priority-fallback-channel-dispatch.md)

## Status

- **Created**: 2026-08-30 (Phase: Intent)
- **Status**: Accepted
- **Approval**: User approved implementation on 2026-08-30.
