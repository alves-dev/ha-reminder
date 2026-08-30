# Decision: Tech Stack

## Context

HA Reminder is distributed as a custom integration and must operate within the
supported Home Assistant runtime and ecosystem.

## Decision

Use Python 3.13 with Home Assistant `2025.12.4` as the runtime. Package the
project as a Home Assistant custom integration, using Home Assistant's built-in
configuration, entity, service, scheduling, and storage APIs. Use `pytest` with
the Home Assistant custom-component test helpers for tests and Ruff for linting.

## Rationale

The manifest, package metadata, and integration modules establish Home Assistant
as the host platform. Its native APIs provide the configuration UI and entity
types this product needs, while its storage and service interfaces keep the
integration local to the user's installation. The exact rationale is not
documented in the existing codebase; it is inferred from the declared runtime
and implementation.

## Alternatives Considered

Alternatives are not documented in the existing codebase. Plausible alternatives
would be a standalone reminder service or a different Home Assistant runtime
version, but neither is implemented.

## Outcomes

Outcomes to be documented as the project evolves.

## Related

- [Project Intent](../intent/project-intent.md)
- [Feature: Per-Person Reminder Lists](../intent/feature-per-person-reminder-lists.md)
- [Feature: Reminder Configuration](../intent/feature-reminder-configuration.md)
- [Decision: Home Assistant Integration Architecture](002-home-assistant-integration-architecture.md)

## Status

- **Created**: 2026-08-30 (Phase: Intent)
- **Status**: Accepted
- **Note**: Documented from existing implementation.
