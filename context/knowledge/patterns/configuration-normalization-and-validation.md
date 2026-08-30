# Pattern: Configuration Normalization and Validation

## Description

Accept user-friendly configuration values at the boundary, validate them, and
convert them once to the canonical values used by runtime code.

## When to Use

Use this when Home Assistant forms collect values whose display format differs
from the durable internal representation, such as intervals expressed in minutes
or hours.

## Pattern

Keep schema construction separate from normalization. Raise a form validation
error for invalid input. Store timing values in seconds so the runtime scheduler
does not need to parse display strings.

## Example

```python
def _normalise(values: dict[str, Any]) -> dict[str, Any]:
    result = dict(values)
    try:
        units = []
        for value in result[CONF_INTERVALS].replace(" ", "").split(","):
            factor = 3600 if value.endswith("h") else 60
            units.append(int(value[:-1]) * factor)
        if not units or min(units) <= 0:
            raise ValueError
    except (AttributeError, ValueError):
        raise vol.Invalid("invalid_intervals") from None
    result[CONF_INTERVALS] = units
    result[CONF_RETRY_INTERVAL] = int(result[CONF_RETRY_INTERVAL]) * 60
    return result
```

## Files Using This Pattern

- `custom_components/ha_reminder/config_flow.py` — builds forms and normalizes timing values before storing them.
- `tests/test_config_and_todo.py` — verifies canonical seconds are produced.

## Related

- [Decision: Home Assistant Integration Architecture](../../decisions/002-home-assistant-integration-architecture.md)
- [Feature: Reminder Configuration](../../intent/feature-reminder-configuration.md)

## Status

- **Created**: 2026-08-30
- **Status**: Active
