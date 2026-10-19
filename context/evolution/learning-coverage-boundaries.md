# Learning: Coverage at Integration Boundaries

## Status

- **Created**: 2026-10-19
- **Status**: Recorded

## Insight

The largest coverage gaps were not in pure reminder models, but at Home
Assistant boundaries: entity setup, manager lifecycle, asynchronous dispatch,
and configuration normalization. Focused tests can exercise these paths with
small manager doubles and real policy inputs, while leaving production code and
Sonar exclusions unchanged.

## Application

Keep boundary tests next to the existing integration tests and cover both the
state exposed to Home Assistant and the callback/service contract used to
mutate it. Treat generated coverage reports as local CI artifacts rather than
repository content.

## Related

- [Decision: SonarQube Analysis Configuration](../decisions/008-sonarqube-analysis.md)
- [Pattern: Manager-Backed Platform Entities](../knowledge/patterns/manager-backed-platform-entities.md)
- [Pattern: Priority Fallback Channel Dispatch](../knowledge/patterns/priority-fallback-channel-dispatch.md)
