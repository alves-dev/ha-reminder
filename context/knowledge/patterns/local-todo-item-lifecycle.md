# Pattern: Local To-Do Item Lifecycle

## Description

Maintain an integration-owned task list as serializable dictionaries while
converting to and from the host platform's native task item model at its API
boundary.

## When to Use

Use this when an integration owns a local task collection and needs to preserve
it across reloads while exposing a standard task-list interface.

## Pattern

Keep one canonical in-memory collection, generate a stable identifier when an
item is created, convert dates without losing date-only precision, and call one
change callback after every create, update, or delete operation.

## Example

```python
async def async_create_todo_item(self, item: TodoItem) -> None:
    data = self._from_item(item)
    data["uid"] = str(uuid4())
    self._items.append(data)
    await self._updated()

async def _updated(self) -> None:
    self.async_write_ha_state()
    await self._changed(self._items)

@staticmethod
def _from_item(item: TodoItem, keep_uid: str | None = None) -> dict[str, Any]:
    return {
        "uid": keep_uid or item.uid,
        "summary": item.summary,
        "description": item.description,
        "status": str(item.status),
        "due": item.due.isoformat() if item.due else None,
    }
```

## Files Using This Pattern

- `custom_components/ha_reminder/todo.py` — owns item mutation and conversion.
- `custom_components/ha_reminder/manager.py` — reconciles the changed serialized collection.
- `tests/test_config_and_todo.py` — checks date-only conversion.

## Related

- [Decision: Home Assistant Integration Architecture](../../decisions/002-home-assistant-integration-architecture.md)
- [Decision: Persistent Reminder Lifecycle](../../decisions/003-persistent-reminder-lifecycle.md)
- [Feature: Per-Person Reminder Lists](../../intent/feature-per-person-reminder-lists.md)

## Status

- **Created**: 2026-08-30
- **Status**: Active
