# Changelog

# 2026-08-31

- Fixed channel delivery to call each script's response-capable named service
  instead of `script.turn_on`; this enables the required `success` response for
  person and advanced reminders.

# 2026-08-31

- Added the root SonarQube project descriptor for `ha-reminder`, including
  Python source and test roots, pytest coverage import, and quality-gate wait.
- Updated the SonarQube GitHub Actions workflow to use the supported Python
  3.13 runtime while retaining its established public SonarQube endpoint.

# 2026-08-31

- Removed the translated base error from channel tests to prevent cached or
  malformed error translations from obscuring the test result. Channel-call
  logs now include the exception message as well as its type.

# 2026-08-31

- Fixed the channel-test failure translation so it no longer treats the script
  response example as an invalid Home Assistant translation placeholder.

# 2026-08-31

- Added a reusable script blueprint for a notification-channel delivery to one
  selected `notify` entity, including contract-compliant script responses and
  distinct manual-test messaging.

# 2026-08-30

- Added a direct notification-channel test in person settings. It invokes only
  the selected script with `is_test: true`, reports the contract result, and
  leaves reminder scheduling and fallback unchanged.

# 2026-08-30

- Refreshed the Home Assistant branding assets with complete light and dark reminder icon and logo variants.

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
