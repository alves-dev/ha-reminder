# Project Intent: HA Reminder

## What

HA Reminder helps a household keep track of outstanding tasks by turning each
pending item in a person's reminder list into a continuing reminder until the
item is completed or removed.

## Why

Single notifications are easy to miss or dismiss. The project provides persistent
follow-up that can reach a person through the notification surfaces available in
their home, while keeping task completion in a familiar per-person list.

## Current State

The initial simple-mode integration is implemented and released as version
`2026.8.0`. It supports one reminder list per configured person, recurring
low-priority reminders, configurable delivery handling, retained state across
restarts, and diagnostic visibility. Advanced per-reminder configuration and
acknowledgement or snooze actions are intentionally not included.

## Current Features

- Per-person reminder lists
- Persistent follow-up scheduling
- Configurable delivery channels and fallback
- Restart-safe reminder state
- Reminder status visibility
- Person and delivery settings

## Status

- **Created**: 2026-08-30 (Phase: Intent)
- **Status**: Active
- **Note**: Generated from existing codebase analysis.
