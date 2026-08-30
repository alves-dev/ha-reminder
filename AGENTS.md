# AGENTS.md

## Setup Commands

- Install: `uv sync --group dev`
- Test: `uv run pytest`
- Lint: `uv run ruff check .`
- Validate: `python3 /home/alves-dev/.codex/skills/home-assistant-integration-standards/scripts/validate_integration_structure.py .`
- Compile: `python3 -m compileall custom_components`
- Local Home Assistant: `dev/start-ha.sh`, `dev/stop-ha.sh`, and `dev/copy-to-core.sh`

There is no separate build artifact for this custom integration. `dev/copy-to-core.sh`
deploys it to the shared local Home Assistant configuration and restarts that
instance. The start and stop helpers manage the shared instance; use them only
when local Home Assistant testing is needed.

## Code Style

- Use Python 3.13 and asynchronous Home Assistant APIs.
- Keep lines at or below 100 characters where practical; Ruff enforces the
  configured lint rules.
- Use type annotations, module and public-member docstrings, and `async_` names
  for asynchronous methods.
- Keep config-entry runtime state in the person-scoped reminder manager.
- Follow patterns from `@context/knowledge/patterns/`.

## Context Files to Load

Before starting any work, load relevant context:

- `@context/.context-mesh-framework.md` (always)
- `@context/intent/project-intent.md` (always)
- `@context/intent/feature-*.md` (for the affected feature)
- `@context/decisions/*.md` (relevant decisions)
- `@context/knowledge/patterns/*.md` (patterns to follow)

## Project Structure

```text
root/
├── AGENTS.md
├── context/
│   ├── .context-mesh-framework.md
│   ├── intent/
│   ├── decisions/
│   ├── knowledge/
│   ├── agents/
│   └── evolution/
├── custom_components/ha_reminder/
├── tests/
├── docs/
└── dev/
```

## AI Agent Rules

### Always

- Load relevant Context Mesh files before implementing.
- Follow accepted decisions in `@context/decisions/`.
- Use applicable patterns from `@context/knowledge/patterns/`.
- Update context after a functional or technical change.

### Never

- Mix technical implementation detail into feature intent files.
- Ignore documented decisions without explicitly superseding them.
- Use documented anti-patterns.
- Leave context stale after a material change.

### After Any Changes

- Update feature intent if user-visible behavior changed.
- Record a new or superseding decision for technical approach changes.
- Add outcomes to relevant decision files when known.
- Update `context/evolution/changelog.md`.
- Create a learning record for significant reusable insight.

## Definition of Done (Build Phase)

Before completing an implementation:

- [ ] Feature intent is current.
- [ ] Required ADR/decision exists before implementation.
- [ ] Code follows documented patterns.
- [ ] Accepted decisions are respected or superseded.
- [ ] Appropriate tests and validation pass.
- [ ] Context reflects the implementation.
- [ ] Context changelog is updated.
