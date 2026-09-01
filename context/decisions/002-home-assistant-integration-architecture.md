# Decision: Home Assistant Integration Architecture

## Context

The product needs separate reminder ownership for each person, a user-facing
configuration workflow, a task surface, and status visibility within Home
Assistant.

## Decision

Model each configured person as one Home Assistant config entry with an
integration-owned device, one local to-do entity, and two sensor entities. Keep
a single runtime manager as the owner of that config entry's reminder state and
share it with the platform entities.

## Rationale

The implementation uses the selected person as the config-entry unique identity
and creates all person-scoped entities under a matching integration device. This
keeps configuration, tasks, scheduling, and diagnostics grouped without treating
the person's existing entity as a physical device. Rationale is inferred from
the config flow and runtime entity setup.

## Alternatives Considered

Alternatives are not documented in the existing codebase. Reasonable alternatives
include one global reminder list, externally provided task lists, or one entity
per reminder; none is selected in the implemented simple mode.

## Outcomes

Superseded on 2026-09-01 by the subentry-based configuration model in
[Decision 009](009-subentry-based-integration-configuration.md). Existing
person configurations are migrated into subentries of one HA Reminder entry.

## Related

- [Project Intent](../intent/project-intent.md)
- [Feature: Per-Person Reminder Lists](../intent/feature-per-person-reminder-lists.md)
- [Feature: Reminder Status Visibility](../intent/feature-reminder-status.md)
- [Feature: Reminder Configuration](../intent/feature-reminder-configuration.md)
- [Feature: Delivery Channel Testing](../intent/feature-delivery-channel-testing.md)
- [Feature: Advanced Reminder Devices](../intent/feature-advanced-reminder-devices.md)
- [Decision: Tech Stack](001-tech-stack.md)
- [Decision: Advanced Reminder Runtime Architecture](006-advanced-reminder-runtime-architecture.md)

## Status

- **Created**: 2026-08-30 (Phase: Intent)
- **Status**: Superseded by Decision 009
- **Note**: Documented from existing implementation.
