# Changelog

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
