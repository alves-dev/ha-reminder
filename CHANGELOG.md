# Changelog

All user-relevant changes are documented in this file.

## [2026.10.2] - 2026-10-21

### Changed

- Clarified progressive interval descriptions with an explicit example showing
  that the sequence does not restart daily and the final interval repeats indefinitely.
- Added the same field descriptions to the person-reminder creation form, not only the edit form.

### Fixed

- Prevented creating more than one person reminder list for the same person by
  excluding already configured people from the creation selector.
- Kept people available for any number of advanced reminder devices.

## [2026.10.1] - 2026-10-19

### Added

- Added a per-person delivery-channel sensor with the channel count and each
  channel's name, priority, and script entity ID as attributes.
- Added descriptions to Person settings for progressive intervals, quiet hours,
  delivery retries, and retry reset behavior.

### Fixed

- Prevented concurrent scheduler callbacks from delivering the same reminder
  more than once.

## [2026.9.0] - 2026-09-01

### Changed

- Corrected the per-person to-do name and removed the low notification level.
- Added notification-level and daily-completion entities to advanced reminder
  devices. Daily completion suppresses reminders through local midnight.
- Added an exact-time follow-up option to advanced reminder configuration.
- Advanced configuration now hides inapplicable schedule fields in a dedicated
  schedule-details step.
- Configurations without schedule-specific fields now save directly instead of
  presenting an empty details step.
- Replaced the configuration-type selector with separate setup actions for
  person reminder lists and advanced reminder devices.
- Grouped existing reminder configurations under one HA Reminder entry while
  retaining their saved reminder state, devices, and entity identifiers.

## [2026.8.0] - 2026-08-30

### Added

- Advanced reminder devices with one-time and recurring schedules, recipient-specific delivery cycles, logical-device entities, and idempotent completion actions.
- Initial simple-mode HA Reminder integration with local to-do lists, persistent schedules, script delivery, fallback, quiet hours, and diagnostic sensors.

### Changed

- Refreshed the Home Assistant branding assets with complete light and dark icon and logo variants.
