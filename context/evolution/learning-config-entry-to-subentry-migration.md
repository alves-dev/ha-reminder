# Learning: Preserve Runtime Identity When Migrating to Config Subentries

## Insight

When independent Home Assistant config entries become subentries, retaining the
former entry ID as each subentry ID preserves state stores and entity unique
identifiers without data copying.

## Evidence

HA Reminder moves each old entry's configuration into a subentry with the same
identifier, then reassigns the associated entity and device registries to the
parent entry and subentry before removing the legacy entry. Removal is deferred
until Home Assistant has finished startup so its setup locks are released.

## Reuse

Use this migration order for integrations adopting native creation actions:
create subentries with stable IDs, transfer registry ownership, then remove old
entries after startup. Keep platform setup at the parent level and associate
each entity with its subentry when adding it.

## Related

- [Decision: Subentry-Based Integration Configuration](../decisions/009-subentry-based-integration-configuration.md)
- [Feature: Reminder Configuration](../intent/feature-reminder-configuration.md)

## Status

- **Created**: 2026-09-01 (Phase: Learn)
- **Status**: Active
