"""Config and options flows for HA Reminder."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    COMPLETION_EXPIRE,
    COMPLETION_UNTIL,
    CONF_ASSIGNMENTS,
    CONF_CHANNELS,
    CONF_COMPLETION_POLICY,
    CONF_ENABLED,
    CONF_ENTRY_TYPE,
    CONF_EXACT_TIME,
    CONF_INTERVAL_DAYS,
    CONF_INTERVALS,
    CONF_LEVEL,
    CONF_MAX_RETRIES,
    CONF_PERSON_ENTITY_ID,
    CONF_QUIET_END,
    CONF_QUIET_START,
    CONF_RECIPIENTS,
    CONF_RECURRENCE_REFERENCE,
    CONF_RETRY_INTERVAL,
    CONF_SCHEDULE_TYPE,
    CONF_START_DATE,
    CONF_TIME_PERIOD,
    CONF_WEEKDAYS,
    DEFAULT_INTERVALS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RETRY_INTERVAL,
    DOMAIN,
    ENTRY_TYPE_ADVANCED,
    ENTRY_TYPE_PERSON,
    LEVEL_CRITICAL,
    LEVEL_HIGH,
    LEVEL_LOW,
    LEVEL_NORMAL,
    MORNING_TIME,
    PERIOD_AFTERNOON,
    PERIOD_EVENING,
    PERIOD_EXACT,
    PERIOD_MORNING,
    REFERENCE_COMPLETION,
    REFERENCE_SCHEDULE,
    SCHEDULE_DAILY,
    SCHEDULE_EVERY_DAYS,
    SCHEDULE_ONCE,
    SCHEDULE_WEEKDAYS,
    SCHEDULE_WEEKLY,
)


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the person-configuration form."""
    defaults = defaults or {}
    return vol.Schema({
        vol.Required(CONF_PERSON_ENTITY_ID, default=defaults.get(CONF_PERSON_ENTITY_ID)): selector.EntitySelector(selector.EntitySelectorConfig(domain="person")),
        vol.Required(CONF_INTERVALS, default=", ".join(f"{v // 60}m" for v in defaults.get(CONF_INTERVALS, DEFAULT_INTERVALS))): str,
        vol.Required(CONF_QUIET_START, default=defaults.get(CONF_QUIET_START, "22:00")): str,
        vol.Required(CONF_QUIET_END, default=defaults.get(CONF_QUIET_END, "07:00")): str,
        vol.Required(CONF_RETRY_INTERVAL, default=defaults.get(CONF_RETRY_INTERVAL, DEFAULT_RETRY_INTERVAL // 60)): selector.NumberSelector(selector.NumberSelectorConfig(min=1, max=120, mode=selector.NumberSelectorMode.BOX)),
        vol.Required(CONF_MAX_RETRIES, default=defaults.get(CONF_MAX_RETRIES, DEFAULT_MAX_RETRIES)): selector.NumberSelector(selector.NumberSelectorConfig(min=0, max=20, mode=selector.NumberSelectorMode.BOX)),
    })


def _person_options_schema(defaults: dict[str, Any]) -> vol.Schema:
    """Build timing options without allowing the configured person to change."""
    display = dict(defaults)
    display[CONF_RETRY_INTERVAL] = defaults.get(CONF_RETRY_INTERVAL, DEFAULT_RETRY_INTERVAL) // 60
    schema = dict(_schema(display).schema)
    del schema[next(key for key in schema if getattr(key, "schema", None) == CONF_PERSON_ENTITY_ID)]
    return vol.Schema(schema)


def _normalise(values: dict[str, Any]) -> dict[str, Any]:
    """Convert person settings to canonical seconds."""
    result = dict(values)
    try:
        units = []
        for value in result[CONF_INTERVALS].replace(" ", "").split(","):
            units.append(int(value[:-1]) * (3600 if value.endswith("h") else 60))
        if not units or min(units) <= 0:
            raise ValueError
    except (AttributeError, ValueError):
        raise vol.Invalid("invalid_intervals") from None
    result[CONF_INTERVALS] = units
    result[CONF_RETRY_INTERVAL] = int(result[CONF_RETRY_INTERVAL]) * 60
    result[CONF_MAX_RETRIES] = int(result[CONF_MAX_RETRIES])
    return result


def _advanced_schema(defaults: dict[str, Any], people: list[str]) -> vol.Schema:
    """Build the advanced-reminder form."""
    people_options = [
        selector.SelectOptionDict(value=person, label=person.split(".", 1)[-1].replace("_", " ").title())
        for person in people
    ]
    return vol.Schema({
        vol.Required("title", default=defaults.get("title", "")): str,
        vol.Required(CONF_RECIPIENTS, default=defaults.get(CONF_RECIPIENTS, people)): selector.SelectSelector(selector.SelectSelectorConfig(options=people_options, multiple=True)),
        vol.Required(CONF_LEVEL, default=defaults.get(CONF_LEVEL, LEVEL_LOW)): selector.SelectSelector(selector.SelectSelectorConfig(options=[
            selector.SelectOptionDict(value=LEVEL_LOW, label="Low"),
            selector.SelectOptionDict(value=LEVEL_NORMAL, label="Normal"),
            selector.SelectOptionDict(value=LEVEL_HIGH, label="High"),
            selector.SelectOptionDict(value=LEVEL_CRITICAL, label="Critical"),
        ])),
        vol.Required(CONF_SCHEDULE_TYPE, default=defaults.get(CONF_SCHEDULE_TYPE, SCHEDULE_ONCE)): selector.SelectSelector(selector.SelectSelectorConfig(options=[
            selector.SelectOptionDict(value=SCHEDULE_ONCE, label="Once"),
            selector.SelectOptionDict(value=SCHEDULE_DAILY, label="Every day"),
            selector.SelectOptionDict(value=SCHEDULE_WEEKLY, label="Every week"),
            selector.SelectOptionDict(value=SCHEDULE_WEEKDAYS, label="Selected weekdays"),
            selector.SelectOptionDict(value=SCHEDULE_EVERY_DAYS, label="Every number of days"),
        ])),
        vol.Required(CONF_START_DATE, default=defaults.get(CONF_START_DATE)): selector.DateSelector(),
        vol.Required(CONF_TIME_PERIOD, default=defaults.get(CONF_TIME_PERIOD, PERIOD_EXACT)): selector.SelectSelector(selector.SelectSelectorConfig(options=[
            selector.SelectOptionDict(value=PERIOD_EXACT, label="Exact time"),
            selector.SelectOptionDict(value=PERIOD_MORNING, label="Morning (09:00)"),
            selector.SelectOptionDict(value=PERIOD_AFTERNOON, label="Afternoon (13:00)"),
            selector.SelectOptionDict(value=PERIOD_EVENING, label="Evening (18:00)"),
        ])),
        vol.Required(CONF_EXACT_TIME, default=defaults.get(CONF_EXACT_TIME, MORNING_TIME)): selector.TimeSelector(),
        vol.Required(CONF_WEEKDAYS, default=defaults.get(CONF_WEEKDAYS, [])): selector.SelectSelector(selector.SelectSelectorConfig(options=[
            selector.SelectOptionDict(value="0", label="Monday"),
            selector.SelectOptionDict(value="1", label="Tuesday"),
            selector.SelectOptionDict(value="2", label="Wednesday"),
            selector.SelectOptionDict(value="3", label="Thursday"),
            selector.SelectOptionDict(value="4", label="Friday"),
            selector.SelectOptionDict(value="5", label="Saturday"),
            selector.SelectOptionDict(value="6", label="Sunday"),
        ], multiple=True)),
        vol.Required(CONF_INTERVAL_DAYS, default=defaults.get(CONF_INTERVAL_DAYS, 1)): selector.NumberSelector(selector.NumberSelectorConfig(min=1, max=3650, mode=selector.NumberSelectorMode.BOX)),
        vol.Required(CONF_COMPLETION_POLICY, default=defaults.get(CONF_COMPLETION_POLICY, COMPLETION_EXPIRE)): selector.SelectSelector(selector.SelectSelectorConfig(options=[
            selector.SelectOptionDict(value=COMPLETION_EXPIRE, label="Expire at the end of the day"),
            selector.SelectOptionDict(value=COMPLETION_UNTIL, label="Keep reminding until completed"),
        ])),
        vol.Required(CONF_RECURRENCE_REFERENCE, default=defaults.get(CONF_RECURRENCE_REFERENCE, REFERENCE_SCHEDULE)): selector.SelectSelector(selector.SelectSelectorConfig(options=[
            selector.SelectOptionDict(value=REFERENCE_SCHEDULE, label="Keep the original schedule"),
            selector.SelectOptionDict(value=REFERENCE_COMPLETION, label="Start the next interval after completion"),
        ])),
        vol.Required(CONF_ENABLED, default=defaults.get(CONF_ENABLED, True)): selector.BooleanSelector(),
    })


def _normalise_advanced(values: dict[str, Any]) -> dict[str, Any]:
    """Validate advanced-reminder cross-field invariants."""
    result = dict(values)
    if not result["title"].strip() or not result[CONF_RECIPIENTS]:
        raise vol.Invalid("invalid_advanced_reminder")
    if result[CONF_COMPLETION_POLICY] == COMPLETION_EXPIRE and result[CONF_RECURRENCE_REFERENCE] == REFERENCE_COMPLETION:
        raise vol.Invalid("invalid_completion_reference")
    if result[CONF_SCHEDULE_TYPE] == SCHEDULE_WEEKDAYS and not result[CONF_WEEKDAYS]:
        raise vol.Invalid("missing_weekdays")
    result[CONF_WEEKDAYS] = [str(day) for day in result[CONF_WEEKDAYS]]
    result[CONF_INTERVAL_DAYS] = int(result[CONF_INTERVAL_DAYS])
    return result


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Create either a person configuration or an advanced reminder device."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        if user_input:
            if user_input[CONF_ENTRY_TYPE] == ENTRY_TYPE_PERSON:
                return await self.async_step_person()
            return await self.async_step_advanced()
        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Required(CONF_ENTRY_TYPE, default=ENTRY_TYPE_PERSON): selector.SelectSelector(
                selector.SelectSelectorConfig(options=[
                    selector.SelectOptionDict(value=ENTRY_TYPE_PERSON, label="Person reminder list"),
                    selector.SelectOptionDict(value=ENTRY_TYPE_ADVANCED, label="Advanced reminder device"),
                ])
            )
        }))

    async def async_step_person(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        errors: dict[str, str] = {}
        if user_input:
            try:
                data = _normalise(user_input)
            except vol.Invalid:
                errors["base"] = "invalid_intervals"
            else:
                data[CONF_ENTRY_TYPE] = ENTRY_TYPE_PERSON
                await self.async_set_unique_id(data[CONF_PERSON_ENTITY_ID])
                self._abort_if_unique_id_configured()
                name = data[CONF_PERSON_ENTITY_ID].split(".", 1)[1].replace("_", " ").title()
                return self.async_create_entry(title=f"Reminders — {name}", data=data)
        return self.async_show_form(step_id="person", data_schema=_schema(), errors=errors)

    def _configured_people(self) -> list[str]:
        return [entry.data[CONF_PERSON_ENTITY_ID] for entry in self.hass.config_entries.async_entries(DOMAIN) if entry.data.get(CONF_ENTRY_TYPE, ENTRY_TYPE_PERSON) == ENTRY_TYPE_PERSON]

    async def async_step_advanced(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        people = self._configured_people()
        if not people:
            return self.async_abort(reason="no_configured_people")
        errors: dict[str, str] = {}
        if user_input:
            try:
                data = _normalise_advanced(user_input)
            except vol.Invalid as err:
                errors["base"] = str(err)
            else:
                data[CONF_ENTRY_TYPE] = ENTRY_TYPE_ADVANCED
                await self.async_set_unique_id(f"advanced-{uuid4()}")
                return self.async_create_entry(title=data["title"].strip(), data=data)
        return self.async_show_form(step_id="advanced", data_schema=_advanced_schema({}, people), errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> OptionsFlow:
        return OptionsFlow()


class OptionsFlow(config_entries.OptionsFlow):
    """Edit person delivery settings or an advanced reminder definition."""

    @property
    def _current(self) -> dict[str, Any]:
        return {**self.config_entry.data, **self.config_entry.options}

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        if self.config_entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_ADVANCED:
            return await self.async_step_advanced()
        return self.async_show_menu(
            step_id="init",
            menu_options=["person", "add_channel", "edit_channel", "test_channel", "remove_channel"],
        )

    async def async_step_person(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        if user_input:
            try:
                data = _normalise({**user_input, CONF_PERSON_ENTITY_ID: self.config_entry.data[CONF_PERSON_ENTITY_ID]})
                data.pop(CONF_PERSON_ENTITY_ID)
                return self.async_create_entry(title="", data={**self.config_entry.options, **data})
            except vol.Invalid:
                return self.async_show_form(step_id="person", data_schema=_person_options_schema(self._current), errors={"base": "invalid_intervals"})
        return self.async_show_form(step_id="person", data_schema=_person_options_schema(self._current))

    async def async_step_advanced(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        people = [entry.data[CONF_PERSON_ENTITY_ID] for entry in self.hass.config_entries.async_entries(DOMAIN) if entry.data.get(CONF_ENTRY_TYPE, ENTRY_TYPE_PERSON) == ENTRY_TYPE_PERSON]
        if user_input:
            try:
                data = _normalise_advanced(user_input)
            except vol.Invalid as err:
                return self.async_show_form(step_id="advanced", data_schema=_advanced_schema(self._current, people), errors={"base": str(err)})
            return self.async_create_entry(title="", data={**self.config_entry.options, **data})
        return self.async_show_form(step_id="advanced", data_schema=_advanced_schema(self._current, people))

    async def async_step_add_channel(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        if user_input:
            current = self._current
            script_id = user_input["script_entity_id"]
            channels = [item for item in current.get(CONF_CHANNELS, []) if item["id"] != script_id]
            channels.append({"id": script_id, "name": user_input["name"], "script_entity_id": script_id, "enabled": user_input["enabled"]})
            assignments = [item for item in current.get(CONF_ASSIGNMENTS, []) if item["channel_id"] != script_id]
            assignments.append({"person_entity_id": current[CONF_PERSON_ENTITY_ID], "channel_id": script_id, "priority": int(user_input["priority"])})
            return self.async_create_entry(title="", data={**self.config_entry.options, CONF_CHANNELS: channels, CONF_ASSIGNMENTS: assignments})
        return self.async_show_form(step_id="add_channel", data_schema=vol.Schema({
            vol.Required("script_entity_id"): selector.EntitySelector(selector.EntitySelectorConfig(domain="script")),
            vol.Required("name"): str,
            vol.Required("priority", default=1): selector.NumberSelector(selector.NumberSelectorConfig(min=1, max=99, mode=selector.NumberSelectorMode.BOX)),
            vol.Required("enabled", default=True): selector.BooleanSelector(),
        }))

    async def async_step_edit_channel(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        """Select an existing channel before showing its editable settings."""
        channels = self._current.get(CONF_CHANNELS, [])
        if not channels:
            return self.async_abort(reason="no_channels")
        if user_input:
            self._editing_channel_id = user_input["channel_id"]
            return await self.async_step_edit_channel_details()
        return self.async_show_form(
            step_id="edit_channel",
            data_schema=vol.Schema(
                {
                    vol.Required("channel_id"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=item["id"], label=item["name"])
                                for item in channels
                            ]
                        )
                    )
                }
            ),
        )

    async def async_step_edit_channel_details(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Update the selected channel without changing its script association."""
        current = self._current
        channel_id = self._editing_channel_id
        channel = next(item for item in current[CONF_CHANNELS] if item["id"] == channel_id)
        assignment = next(
            item for item in current.get(CONF_ASSIGNMENTS, []) if item["channel_id"] == channel_id
        )
        if user_input:
            channels = [item for item in current[CONF_CHANNELS] if item["id"] != channel_id]
            channels.append(
                {
                    **channel,
                    "name": user_input["name"],
                    "enabled": user_input["enabled"],
                }
            )
            assignments = [
                item for item in current.get(CONF_ASSIGNMENTS, []) if item["channel_id"] != channel_id
            ]
            assignments.append({**assignment, "priority": int(user_input["priority"])})
            return self.async_create_entry(
                title="",
                data={**self.config_entry.options, CONF_CHANNELS: channels, CONF_ASSIGNMENTS: assignments},
            )
        return self.async_show_form(
            step_id="edit_channel_details",
            data_schema=vol.Schema(
                {
                    vol.Required("name", default=channel["name"]): str,
                    vol.Required("priority", default=assignment.get("priority", 1)): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1, max=99, mode=selector.NumberSelectorMode.BOX
                        )
                    ),
                    vol.Required("enabled", default=channel.get("enabled", True)): selector.BooleanSelector(),
                }
            ),
        )

    async def async_step_remove_channel(self, user_input: dict[str, Any] | None = None) -> config_entries.FlowResult:
        current = self._current
        channels = current.get(CONF_CHANNELS, [])
        if not channels:
            return self.async_abort(reason="no_channels")
        if user_input:
            channel_id = user_input["channel_id"]
            return self.async_create_entry(title="", data={**self.config_entry.options, CONF_CHANNELS: [item for item in channels if item["id"] != channel_id], CONF_ASSIGNMENTS: [item for item in current.get(CONF_ASSIGNMENTS, []) if item["channel_id"] != channel_id]})
        return self.async_show_form(step_id="remove_channel", data_schema=vol.Schema({
            vol.Required("channel_id"): selector.SelectSelector(selector.SelectSelectorConfig(options=[selector.SelectOptionDict(value=item["id"], label=item["name"]) for item in channels]))
        }))

    async def async_step_test_channel(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Invoke exactly one configured channel without creating a reminder."""
        channels = self._current.get(CONF_CHANNELS, [])
        if not channels:
            return self.async_abort(reason="no_channels")

        result = "Not run yet."
        selected_channel_id = None
        if user_input:
            selected_channel_id = user_input["channel_id"]
            success = await self.config_entry.runtime_data.async_test_channel(selected_channel_id)
            if success:
                result = "Success: the script confirmed delivery."
            else:
                result = "Failed: the script did not confirm delivery."

        channel_field = (
            vol.Required("channel_id", default=selected_channel_id)
            if selected_channel_id
            else vol.Required("channel_id")
        )

        return self.async_show_form(
            step_id="test_channel",
            data_schema=vol.Schema(
                {
                    channel_field: selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=item["id"], label=item["name"])
                                for item in channels
                            ]
                        )
                    )
                }
            ),
            description_placeholders={"result": result},
        )
