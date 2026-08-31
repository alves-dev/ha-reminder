# Learning: Shared Completion Needs a Distinct Occurrence Generation

## Insight

A recurring shared reminder needs two layers of state: one occurrence that can
be completed globally and one delivery cycle for every recipient. A single
generation on the occurrence makes cancellation, editing, expiry and completion
safe without forcing each recipient to invent a separate reminder identity.

## Evidence

Advanced occurrence state persists a generation with its recipient map. Every
delivery checks that generation before and after asynchronous channel work.
Completion clears the active occurrence and increments the generation, so late
channel responses cannot create a follow-up after a shared completion.

## Reuse

Use this structure for future reminder interactions such as snooze and
acknowledgement, and for other fan-out workflows that share one terminal
outcome while retaining per-recipient delivery policy.

## Related

- [Feature: Advanced Reminder Devices](../intent/feature-advanced-reminder-devices.md)
- [Decision: Advanced Reminder Runtime Architecture](../decisions/006-advanced-reminder-runtime-architecture.md)
- [Pattern: Reminder Generation Reconciliation](../knowledge/patterns/reminder-generation-reconciliation.md)

## Status

- **Created**: 2026-08-30 (Phase: Learn)
- **Status**: Active
