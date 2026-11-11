# Decision: Conditional Advanced Reminder Form

## Context

Home Assistant Core 2026.11 added conditional visibility for fields in config
flows and options flows. HA Reminder's advanced-reminder flow currently uses a
second form to collect fields that depend on the selected schedule, time, and
completion policy.

## Decision

Use Home Assistant's `visible` conditions to keep the advanced-reminder
configuration in one form. Show schedule-specific fields only when their
controlling selection makes them applicable, while retaining integration-side
cross-field validation and canonical defaults.

Raise the minimum supported Home Assistant version to 2026.11.0.

## Rationale

The native conditional form removes an unnecessary submit-and-next-screen step,
keeps the user in one configuration context, and lets Home Assistant omit hidden
fields from submitted input. The integration must still validate combinations
because visibility is a user-interface concern, not a replacement for runtime
validation.

## Alternatives Considered

- Keep the two-step flow. This remains compatible with older Home Assistant
  versions but provides a less direct configuration experience.
- Build a custom frontend form. This would duplicate native Home Assistant
  behavior and add maintenance cost.

## Outcomes

The advanced form now conditionally displays exact-time, weekdays, every-days,
and completion-reference fields in one screen. The old details step and its
temporary flow state are removed. Reconfiguration continues to normalize missing
conditional inputs using safe defaults.

## Related

- [Feature: Reminder Configuration](../intent/feature-reminder-configuration.md)
- [Decision: Advanced Daily Completion and Exact-Time Follow-Up](010-advanced-daily-completion-and-exact-time-follow-up.md)
- [Pattern: Configuration Normalization and Validation](../knowledge/patterns/configuration-normalization-and-validation.md)

## Status

- **Created**: 2026-11-11
- **Status**: Accepted and implemented
- **Supersedes**: Decision 010's two-step advanced-form approach
