# Pattern: Reminder Generation Reconciliation

## Description

Reconcile durable reminder records against the current task collection and use a
generation number to reject asynchronous results that belong to an older version
of an item.

## When to Use

Use this when tasks can change while background work is already underway and a
late result must not restore or reschedule obsolete state.

## Pattern

Build a map of pending items, remove records that are no longer pending, replace
records that have changed, and increment their generation. Capture that generation
when dispatching work and compare it again before committing the result.

## Example

```python
for uid in set(self.reminders) - set(pending):
    self.reminders.pop(uid, None)
for uid, item in pending.items():
    existing = self.reminders.get(uid)
    if existing is None or self._changed(existing, item):
        self.reminders[uid] = self._new_reminder(
            item, now, (existing.generation + 1 if existing else 1)
        )

current = self.reminders.get(uid)
if not current or current.generation != generation:
    return
```

## Files Using This Pattern

- `custom_components/ha_reminder/manager.py` — reconciles task changes and guards delivery completion.
- `custom_components/ha_reminder/models.py` — persists the generation on every reminder record.

## Related

- [Decision: Persistent Reminder Lifecycle](../../decisions/003-persistent-reminder-lifecycle.md)
- [Feature: Restart-Safe Reminders](../../intent/feature-restart-safe-reminders.md)

## Status

- **Created**: 2026-08-30
- **Status**: Active
