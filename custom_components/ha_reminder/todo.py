"""Local per-person to-do list."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import date, datetime
from typing import Any
from uuid import uuid4

from homeassistant.components.todo import TodoItem, TodoListEntity
from homeassistant.components.todo.const import TodoItemStatus, TodoListEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

ChangedCallback = Callable[[list[dict[str, Any]]], Awaitable[None]]


class ReminderTodoList(TodoListEntity):
    """An integration-owned local todo list."""

    _attr_has_entity_name = True
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.SET_DUE_DATE_ON_ITEM
        | TodoListEntityFeature.SET_DUE_DATETIME_ON_ITEM
        | TodoListEntityFeature.SET_DESCRIPTION_ON_ITEM
    )

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        person_entity_id: str,
        person_name: str,
        initial_items: list[dict[str, Any]],
        changed: ChangedCallback,
    ) -> None:
        self.hass = hass
        self._items = initial_items
        self._changed = changed
        slug = person_entity_id.split(".", 1)[-1]
        self._attr_unique_id = f"{entry_id}_{slug}_todo"
        self._attr_name = f"Reminders {person_name}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=f"Reminders — {person_name}",
            manufacturer="HA Reminder",
            model="Person reminder configuration",
        )

    @property
    def todo_items(self) -> list[TodoItem]:
        """Return to-do items in the native Home Assistant representation."""
        return [self._to_item(item) for item in self._items]

    async def async_create_todo_item(self, item: TodoItem) -> None:
        data = self._from_item(item)
        data["uid"] = str(uuid4())
        self._items.append(data)
        await self._updated()

    async def async_update_todo_item(self, item: TodoItem) -> None:
        if not item.uid:
            return
        for current in self._items:
            if current["uid"] == item.uid:
                current.update(self._from_item(item, keep_uid=item.uid))
                break
        await self._updated()

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        self._items[:] = [item for item in self._items if item["uid"] not in uids]
        await self._updated()

    async def _updated(self) -> None:
        self.async_write_ha_state()
        await self._changed(self._items)

    @staticmethod
    def _to_item(data: dict[str, Any]) -> TodoItem:
        raw_due = data.get("due")
        due = None
        if raw_due:
            due = datetime.fromisoformat(raw_due) if "T" in raw_due else date.fromisoformat(raw_due)
        return TodoItem(
            uid=data["uid"],
            summary=data["summary"],
            description=data.get("description"),
            status=TodoItemStatus(data.get("status", TodoItemStatus.NEEDS_ACTION)),
            due=due,
        )

    @staticmethod
    def _from_item(item: TodoItem, keep_uid: str | None = None) -> dict[str, Any]:
        return {
            "uid": keep_uid or item.uid,
            "summary": item.summary,
            "description": item.description,
            "status": str(item.status),
            "due": item.due.isoformat() if item.due else None,
        }


async def async_setup_entry(
    hass: HomeAssistant, entry: Any, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the per-person todo entity."""
    async_add_entities([entry.runtime_data.todo])
