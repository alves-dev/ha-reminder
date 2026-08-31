# HA Reminder

![Version](https://img.shields.io/badge/Version-2026.8.0-41BDF5?style=flat-square)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.12%2B-41BDF5?logo=homeassistant)
[![Quality Gate](https://sonar.alves-dev.com/api/project_badges/measure?project=ha-reminder&metric=alert_status)](https://sonar.alves-dev.com/dashboard?id=ha-reminder)
[![Coverage](https://sonar.alves-dev.com/api/project_badges/measure?project=ha-reminder&metric=coverage)](https://sonar.alves-dev.com/dashboard?id=ha-reminder)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=alves-dev&repository=ha-reminder&category=integration)

HA Reminder turns each item in a person's local reminder list into a persistent reminder. It also provides dedicated devices for shared or recurring advanced reminders. Delivery stays script-based, so the integration does not need to know whether a script reaches a phone, television, speaker, or another surface.

## Features

- A dedicated `todo` list, pending-count sensor, and next-reminder sensor for every configured person.
- Independent progressive schedules, due-date scheduling (date-only is 09:00), quiet hours, and retry handling.
- Script-only notification channels with per-person priority, fallback, equal-priority round robin, a five-second response timeout, and global five-second channel throttling.
- Local persistent state that is reconciled after Home Assistant restarts.
- Advanced reminder devices with an enable switch, status, next-occurrence visibility, recurrence, independent delivery for each recipient, and shared completion.

## HACS availability

This integration is not available in HACS's default catalog. Install it as an HACS custom repository: add `alves-dev/ha-reminder`, choose the Integration category, download it, and restart Home Assistant. Alternatively, copy `custom_components/ha_reminder` to your Home Assistant configuration directory.

## Configuration and use

Add **HA Reminder** from Settings → Devices & services and choose **Person** to set up a person's reminder list and delivery policy. The integration creates a device named `Reminders — <person>`, a `todo.reminders_<person>` list, and two sensors.

Create pending items in that to-do list as usual. Completing or deleting an item stops its future deliveries. Configure notification channels through the integration options; each channel is a `script.*` that receives the documented payload and returns `{success: true}` when it has dispatched the message.

Choose **Advanced reminder** to create a device for a one-time or recurring household reminder. Select recipients from the people already configured in HA Reminder, define its priority and schedule, then use its enable switch and status sensors. Call `ha_reminder.interact` with `interaction: complete` to complete the active occurrence from an automation, script, actionable notification, or another Home Assistant surface. Snooze and acknowledgement actions are reserved for a future release.

## Technical documentation

- [Channel contract and scheduling behavior](docs/architecture.md)
- [Compatibility](docs/compatibility.md)
- [Development and validation](docs/development.md)
- [Changelog](CHANGELOG.md)
