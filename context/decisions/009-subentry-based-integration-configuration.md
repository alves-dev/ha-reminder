# Decision: Subentry-Based Integration Configuration

## Context

HA Reminder currently represents every person reminder list and every advanced
reminder device as an independent config entry. This prevents Home Assistant
from presenting their creation actions together on one integration page.

## Decision

Represent HA Reminder as one primary config entry with two Home Assistant
config subentry types: person reminder lists and advanced reminder devices.
The integration page exposes one creation action for each subentry type.

Migrate existing independent entries into subentries of one primary entry while
retaining their configuration and stable identifiers for persisted runtime data.

## Rationale

Home Assistant renders creation actions on an integration page from supported
subentry types, as used by integrations such as Ollama. A primary entry makes
the person's reminder lists and advanced reminder devices discoverable from
one place without changing their distinct runtime lifecycles.

## Alternatives Considered

- Keep separate config entries and use the initial config-flow menu. This
  changes only the add-integration wizard and does not provide the requested
  integration-page actions.
- Add a custom frontend panel. This would duplicate native Home Assistant
  configuration behavior and create unnecessary maintenance work.

## Outcomes

The integration page now declares person and advanced reminder subentry types,
which Home Assistant renders as distinct creation actions. Legacy entries are
migrated under one parent entry while retaining their former entry identifiers
as subentry identifiers, preserving reminder storage, entity unique IDs, and
device identifiers. Registry ownership is reassigned before legacy entries are
removed after startup.

## Related

- [Project Intent](../intent/project-intent.md)
- [Feature: Per-Person Reminder Lists](../intent/feature-per-person-reminder-lists.md)
- [Feature: Advanced Reminder Devices](../intent/feature-advanced-reminder-devices.md)
- [Feature: Reminder Configuration](../intent/feature-reminder-configuration.md)
- [Decision: Home Assistant Integration Architecture](002-home-assistant-integration-architecture.md)
- [Decision: Advanced Reminder Runtime Architecture](006-advanced-reminder-runtime-architecture.md)
- [Learning: Config-Entry to Subentry Migration](../evolution/learning-config-entry-to-subentry-migration.md)

## Status

- **Created**: 2026-09-01 (Phase: Intent)
- **Status**: Accepted
- **Approval**: User approved the migration on 2026-09-01.
