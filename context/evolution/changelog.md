# Changelog

# 2026-08-30

- Replaced technical configuration values with human-readable labels and added contextual form
  descriptions for timing, recurrence, delivery channels, and destructive channel removal.

# 2026-08-30

- Added an explicit channel-editing flow that lets users select and update an existing channel.

# 2026-08-30

- Added the runtime English translation bundle so Home Assistant renders configuration and
  options-flow labels for the custom integration.

# 2026-08-30

- Implemented advanced reminder devices with scheduling, recurrence, recipient-specific delivery,
  logical-device entities, an enable switch, and the generic completion action.

# 2026-08-30

- Fixed progressive scheduling so the interval after a successful initial reminder advances to
  the next configured interval.
- Preserved reminder generations after completion or deletion, preventing stale queued work from
  affecting a reopened item with the same identifier.
- Distinguished missing channel setup from temporarily unavailable scripts, and added repair
  warnings for missing setup or removed scripts.
- Cleared integration-owned persisted reminder data when a person configuration is removed.

## [Current State] - Context Mesh Added

### Existing Features (documented)

- Per-person reminder lists — individual outstanding tasks receive follow-up.
- Persistent follow-up scheduling — progressive timing, due dates, quiet hours, and retries.
- Configurable delivery fallback — prioritized routes with failure fallback.
- Restart-safe reminders — durable state and task reconciliation.
- Reminder status visibility — outstanding count and next follow-up status.
- Reminder configuration — person, timing, and delivery settings.

### Tech Stack (documented)

- Python 3.13
- Home Assistant 2025.12.4 custom integration APIs
- Pytest with Home Assistant custom-component helpers
- Ruff

### Patterns Identified

- Configuration normalization and validation
- Local to-do item lifecycle
- Reminder generation reconciliation
- Serialized reminder scheduling
- Priority fallback channel dispatch
- Manager-backed platform entities

---

*Context Mesh added: 2026-08-30*
*This changelog documents the state when Context Mesh was added.*
*Future changes will be tracked below.*
