"""Constants for HA Reminder."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "ha_reminder"
NAME = "HA Reminder"
INTEGRATION_VERSION = "2026.9.0"
PERSON_PLATFORMS = ["todo", "sensor"]
ADVANCED_PLATFORMS = ["sensor", "switch"]

CONF_PERSON_ENTITY_ID = "person_entity_id"
CONF_PERSON_ID = "person_id"
CONF_INTERVALS = "intervals"
CONF_QUIET_START = "quiet_start"
CONF_QUIET_END = "quiet_end"
CONF_RETRY_INTERVAL = "retry_interval"
CONF_MAX_RETRIES = "max_retries"
CONF_CHANNELS = "channels"
CONF_ASSIGNMENTS = "assignments"
CONF_ENTRY_TYPE = "entry_type"
ENTRY_TYPE_PERSON = "person"
ENTRY_TYPE_ADVANCED = "advanced"
CONF_RECIPIENTS = "recipients"
CONF_LEVEL = "level"
CONF_SCHEDULE_TYPE = "schedule_type"
CONF_START_DATE = "start_date"
CONF_TIME_PERIOD = "time_period"
CONF_EXACT_TIME = "exact_time"
CONF_WEEKDAYS = "weekdays"
CONF_INTERVAL_DAYS = "interval_days"
CONF_COMPLETION_POLICY = "completion_policy"
CONF_RECURRENCE_REFERENCE = "recurrence_reference"
CONF_ENABLED = "enabled"
CONF_CONTINUE_AFTER_EXACT_TIME = "continue_after_exact_time"

LEVEL_NORMAL = "normal"
LEVEL_HIGH = "high"
LEVEL_CRITICAL = "critical"
COMPLETION_EXPIRE = "expire_at_end_of_day"
COMPLETION_UNTIL = "until_completed"
REFERENCE_SCHEDULE = "schedule"
REFERENCE_COMPLETION = "completion"
SCHEDULE_ONCE = "once"
SCHEDULE_DAILY = "daily"
SCHEDULE_WEEKLY = "weekly"
SCHEDULE_WEEKDAYS = "weekdays"
SCHEDULE_EVERY_DAYS = "every_days"
PERIOD_EXACT = "exact"
PERIOD_MORNING = "morning"
PERIOD_AFTERNOON = "afternoon"
PERIOD_EVENING = "evening"

DEFAULT_INTERVALS = [900, 1800, 3600, 14400]
DEFAULT_RETRY_INTERVAL = 300
DEFAULT_MAX_RETRIES = 3
CHANNEL_TIMEOUT = timedelta(seconds=5)
CHANNEL_COOLDOWN = timedelta(seconds=5)
MORNING_TIME = "09:00"
AFTERNOON_TIME = "13:00"
EVENING_TIME = "18:00"
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.reminders"
ADVANCED_STORAGE_KEY = f"{DOMAIN}.advanced"
SERVICE_INTERACT = "interact"
INTERACTION_COMPLETE = "complete"
INTERACTION_SNOOZE = "snooze"
INTERACTION_ACKNOWLEDGE = "acknowledge"
INTERACTION_DISMISS = "dismiss"
