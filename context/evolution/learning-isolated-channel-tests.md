# Learning: Isolated Tests Can Reuse a Delivery Boundary Safely

## Insight

A configuration-time action can validate a real asynchronous delivery boundary
without becoming a synthetic domain event. Give it an explicit test marker,
reuse only the concurrency and contract safeguards, and leave lifecycle policy
outside the action.

## Evidence

The channel test invokes one selected script with `is_test: true`, while normal
reminder delivery still owns quiet-hour checks, fallback selection, retry
counts, and schedule updates. Both paths share the script lock, cooldown,
timeout, and `success` response validation.

## Reuse

Apply this split to manual tests of other external actions, such as device
commands or webhook dispatch: call the true integration boundary, preserve its
resource protections, and avoid generating or mutating business state.

## Related

- [Feature: Delivery Channel Testing](../intent/feature-delivery-channel-testing.md)
- [Decision: Isolated Delivery Channel Tests](../decisions/007-isolated-delivery-channel-tests.md)
- [Pattern: Priority Fallback Channel Dispatch](../knowledge/patterns/priority-fallback-channel-dispatch.md)

## Status

- **Created**: 2026-08-30 (Phase: Learn)
- **Status**: Active
