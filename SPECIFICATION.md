# Home Assistant Reminder Integration — Specification

## 1. Document status

This document consolidates the functional and technical decisions made so far for a new Home Assistant reminder integration.

The integration name is **HA Reminder** and its domain is `ha_reminder`.

The product is planned with two usage models:

1. **Simple mode:** each configured person receives a dedicated to-do list. Every pending item becomes a low-level reminder managed automatically by the integration.
2. **Advanced mode:** each reminder is represented by its own logical device and can define recipients, importance, schedule, recurrence and activation state.

The MVP described in detail here is the **simple mode**. Some contracts already include fields needed by advanced mode so the architecture can evolve without breaking changes.

---

## 2. Problem statement

Conventional reminder applications often send a single phone notification. During a busy day, that notification can be dismissed or overlooked and the task is forgotten.

This integration must provide a reminder mechanism that continues trying to reach the responsible person until the associated task is completed. It must take advantage of Home Assistant's available notification surfaces, such as:

- mobile phones;
- computers;
- televisions;
- Alexa or other voice assistants;
- wall tablets;
- any other destination that can be implemented through a Home Assistant script.

The integration must not contain implementation-specific knowledge about Alexa, televisions, mobile applications or other notification technologies.

---

## 3. Existing Home Assistant features used as references

No existing integration evaluated so far provides the complete proposed workflow. However, the following Home Assistant features are useful architectural references:

- **Local To-do:** provides local `todo.*` entities and item lifecycle operations.
- **Alert:** provides repeated notifications, acknowledgement and progressive repeat intervals for entity conditions.
- **Notify and Persistent Notification:** provide generic notification delivery mechanisms.
- **Companion App actionable notifications:** allow actions such as completing or postponing a reminder from a mobile notification.
- **Todoist and Google Tasks:** demonstrate external task providers exposed as Home Assistant to-do entities.

The intended differentiation is not simply task storage. It is a **reminder manager with delivery tracking, fallback channels and persistent follow-up**.

---

## 4. Core concepts

### 4.1 Person configuration

The user selects one or more existing Home Assistant `person.*` entities to be managed by the integration.

For every selected person, the integration creates a logical device in the Home Assistant device registry. This is a configuration device owned by the integration, not a physical device and not a conversion of the existing `person.*` entity into a device.

Example:

```text
person.igor
    └── Device: Reminders — Igor
        ├── todo.reminders_igor
        ├── sensor.igor_pending_reminders
        └── sensor.igor_next_reminder
```

The configuration device stores or references:

- the associated `person.*` entity;
- progressive notification intervals;
- delivery retry policy;
- quiet hours;
- assigned notification channels and their priority for that person.

The state of `person.*`, such as `home`, `not_home` or `unknown`, does not directly block notifications. A channel script may use presence as part of its own delivery logic.

### 4.2 To-do list per person

Each configured person receives one dedicated to-do list, for example:

```text
todo.reminders_igor
todo.reminders_jade
```

Every item in that list belongs to its associated person. A pending item is automatically managed by the reminder engine.

Simple-mode to-do items always have notification level `LOW`.

When an item is marked as completed or removed, all future alerts and queued executions associated with it must stop.

### 4.3 Reminder instance

Each to-do item is managed independently. The integration must not treat the entire list as a single reminder cycle.

Internal state for an item may include:

```yaml
item_uid: "todo-provider-item-id"
reminder_id: "integration-generated-stable-id"
person_entity_id: "person.igor"
todo_entity_id: "todo.reminders_igor"
title: "Buy pet food"
description: "Buy Mel's usual food"
level: "low"
created_at: "2026-08-29T09:00:00Z"
due_at: null
notification_cycle: 1
delivery_retry_count: 0
last_attempt_at: null
last_delivered_at: null
last_successful_channel_id: null
next_notification_at: "2026-08-29T09:15:00Z"
status: "pending"
```

This is internal persistence and does not require one Home Assistant entity per simple to-do item.

### 4.4 Notification level

The common contract supports the following levels:

```text
LOW
NORMAL
HIGH
CRITICAL
```

Simple-mode items always use `LOW`. Advanced mode will allow other levels.

Notification level affects behavior such as quiet-hours handling and may also be interpreted by channel scripts to choose visual style, sound, persistence or urgency.

---

## 5. Notification channels

### 5.1 Definition

A notification channel is always implemented as a Home Assistant `script.*` entity.

The integration calls the configured script using a standard input contract and waits for a response. The script hides all destination-specific implementation details and reports whether it was able to dispatch the notification.

Examples:

```text
script.reminder_mobile_igor
script.reminder_computer_igor
script.reminder_tv_living_room
script.reminder_alexa_living_room
```

### 5.2 Channel configuration

A channel has its own reusable configuration:

```yaml
id: "living_room_tv"
name: "Living room TV"
script_entity_id: "script.reminder_tv_living_room"
enabled: true
```

A channel can be associated with more than one person.

### 5.3 Person-channel assignment

Priority belongs to the relationship between a person and a channel, not to the channel itself. This allows a shared channel to have a different position for each person.

```yaml
assignments:
  - person_entity_id: "person.igor"
    channel_id: "mobile_igor"
    priority: 1
  - person_entity_id: "person.igor"
    channel_id: "living_room_tv"
    priority: 3
  - person_entity_id: "person.jade"
    channel_id: "mobile_jade"
    priority: 1
  - person_entity_id: "person.jade"
    channel_id: "living_room_tv"
    priority: 2
```

Example outcome:

```text
Igor
1. Mobile phone
2. Computer
3. Living room TV
4. Alexa

Jade
1. Mobile phone
2. Living room TV
3. Alexa
```

### 5.4 Input contract

The integration passes a standard payload to every channel script:

```yaml
reminder_id: "01JEXAMPLE"
person_entity_id: "person.igor"
todo_entity_id: "todo.reminders_igor"
todo_item_uid: "provider-item-id"
title: "Buy pet food"
description: "Buy Mel's usual food"
level: "low"
attempt: 2
channel_priority: 1
created_at: "2026-08-29T09:00:00Z"
due_at: null
```

The script is responsible for presentation. It can decide how to combine the title and description, whether to use sound, whether to display an actionable notification and how to interpret the level.

The integration should keep the fields semantically stable. New optional fields may be added later without changing existing meanings.

### 5.5 Response contract

Successful delivery:

```yaml
success: true
```

Failed delivery:

```yaml
success: false
reason: "tv_off"
```

`success: true` means only that the channel successfully dispatched the notification. It does not mean the person read, acknowledged or completed the reminder.

The following conditions are treated as channel failure:

- `success: false`;
- missing response;
- missing `success` field;
- `success` value that is not boolean;
- script unavailable or removed;
- script timeout;
- exception during script execution;
- malformed response.

On failure, the integration records a diagnostic log and continues through the fallback strategy.

The integration must call the script while waiting for its response, using Home Assistant's script service-response support.

### 5.6 Channel timeout

Every channel invocation has a fixed timeout of **5 seconds**. This value is not configurable in the MVP.

A slow or broken channel must not block the entire reminder engine. Timeout is treated as delivery failure and triggers fallback.

---

## 6. Channel selection and fallback

For each notification cycle, the integration performs the following steps:

1. Load channels assigned to the reminder's person.
2. Ignore disabled or unavailable channel configurations.
3. Group the remaining channels by ascending priority.
4. Choose any channel from the lowest numeric priority group.
5. Execute it and validate the response.
6. If it succeeds, stop the current cycle.
7. If it fails, try the other channels with the same priority.
8. If all channels in that priority fail, continue to the next numeric priority.
9. If every assigned channel fails, apply the complete-delivery-failure policy.

Lower numbers represent preferred channels. Priority starts at `1`.

Duplicate priorities are allowed and represent equivalent alternatives. The integration does not need to prevent duplicate priorities. Equal-priority channels use round-robin selection to avoid always favoring the same channel. The round-robin cursor does not need to survive Home Assistant restart.

Example:

```text
Priority 1: Mobile, Computer
Priority 2: TV
Priority 3: Alexa
```

If Mobile fails, the integration tries Computer before proceeding to TV. The first `success: true` ends the cycle; remaining channels are not called.

At every later notification cycle, selection begins again at the lowest numeric priority.

---

## 7. Five-second channel execution protection

The same channel must not be invoked twice within a five-second interval.

This restriction is global per channel, including when the channel is shared by multiple people or several reminders become due simultaneously.

Example:

```text
09:00:00 → Mobile Igor receives Item A
09:00:05 → Mobile Igor receives Item B
09:00:10 → Mobile Igor receives Item C
```

An invocation waiting for the five-second window is queued. It is not considered a failure and must not trigger fallback solely because it is waiting.

Different channels may run concurrently, subject to their own execution state and Home Assistant script mode.

The five-second interval is fixed in the MVP. It may become configurable later.

The channel dispatcher must serialize queued work safely and avoid races when reminders for multiple people reference the same shared channel.

---

## 8. Scheduling in simple mode

### 8.1 Progressive intervals per person

Every person defines a non-empty ordered sequence of intervals. Proposed default:

```text
15 minutes → 30 minutes → 1 hour → 4 hours
```

After reaching the final value, the final interval repeats until the item is completed or removed.

### 8.2 Item without due date and time

For a simple item without a due date/time:

```text
first notification = item creation time + first configured interval
```

Using the default sequence:

```text
09:00 → item created
09:15 → first notification
09:45 → second notification
10:45 → third notification
14:45 → fourth notification
18:45 → final interval repeats
```

There is no immediate notification at creation time.

### 8.3 Item with due date and exact time

When an item contains a due date and exact time:

```text
first notification = due date and time
```

The first configured interval is applied only after that initial due-time notification is successfully delivered.

Example:

```text
18:00 → item becomes due and first notification is delivered
18:15 → second notification
18:45 → third notification
19:45 → fourth notification
23:45 → final interval repeats
```

An item created with an already-expired due date/time is eligible for notification immediately, subject to quiet hours and channel queueing.

### 8.4 Item with date but no time

An item with a date but no time uses the fixed **morning reference time of 09:00** on that date.

Example:

```yaml
morning_reference_time: "09:00"
```

### 8.5 Advancing the sequence

The progressive sequence advances only after at least one channel returns `success: true`.

If every channel fails, the sequence does not advance.

### 8.6 Independent scheduling

Every item maintains an independent sequence and next-notification time.

```text
Item A created at 09:00 → first notification at 09:15
Item B created at 09:10 → first notification at 09:25
```

Items are never combined into a single notification in the MVP.

---

## 9. Complete delivery failure

Proposed defaults:

```yaml
delivery_retry_interval: "5m"
max_delivery_retries: 3
```

If every assigned channel fails during a cycle:

1. Do not advance the progressive interval sequence.
2. Schedule another delivery attempt after five minutes.
3. Start again from the lowest channel priority.
4. Continue respecting quiet hours for `LOW` and `NORMAL` reminders.
5. Repeat up to three short delivery retries.

After three consecutive short retries fail:

1. Reset the short retry counter.
2. Schedule the next attempt using the person's first progressive interval.
3. Keep the item pending indefinitely.

No reminder is discarded because delivery failed.

---

## 10. Quiet hours

Quiet hours are configured per person and are included in the MVP.

```yaml
quiet_hours:
  start: "22:00"
  end: "07:00"
```

Behavior by notification level:

| Level | Respects quiet hours |
| --- | --- |
| `LOW` | Yes |
| `NORMAL` | Yes |
| `HIGH` | No |
| `CRITICAL` | No |

Because simple-mode to-do items are always `LOW`, they do not invoke channels during quiet hours.

While a reminder is suppressed by quiet hours:

- it remains pending;
- its progressive sequence does not advance;
- it is not considered a delivery failure;
- short retry counters do not increase.

When quiet hours end:

1. Every overdue item becomes eligible for immediate queueing.
2. Items remain separate.
3. The five-second per-channel restriction continues to apply.
4. The progressive sequence advances only after successful delivery.

The implementation must correctly handle quiet-hour ranges that cross midnight.

---

## 11. Item lifecycle

### 11.1 Creation

When the integration detects a new pending item:

1. Create its internal reminder state.
2. Assign level `LOW`.
3. Calculate the first notification using its due information or creation time.
4. Persist the state.

### 11.2 Editing

Any functional modification makes the item behave as new and restarts its reminder cycle.

The integration should compare at least:

```text
title
description
due date/time
status
```

When one of these fields changes:

- reset the notification cycle;
- reset delivery retries;
- clear previous delivery history used for scheduling;
- recalculate the first notification;
- use the modification detection time as the new logical creation time when no due time exists.

Synchronizations or refreshes that do not change functional fields must not restart the cycle.

### 11.3 Completion

When an item is marked completed:

- cancel its scheduled execution;
- remove it from channel queues when it has not started execution;
- stop future delivery attempts;
- update person sensors;
- retain only whatever minimal history is required for consistency or diagnostics.

There are no integration events required in the MVP.

### 11.4 Removal

When an item is removed, its reminder state and queued future work are cancelled.

### 11.5 Reopening

When a completed item becomes pending again, it is treated as new and its sequence restarts.

### 11.6 Completion during active execution

If an item is completed while its channel script is already executing, the integration cannot guarantee that the in-flight external notification can be recalled. It must ignore the result for future scheduling and must not schedule another cycle.

---

## 12. Multiple pending items

Every item is delivered separately. The integration does not aggregate several tasks into a summary message in the MVP.

Reasons:

- independent schedules remain correct;
- each channel invocation has a clear `reminder_id`;
- future completion or snooze actions can target one item;
- channel response and delivery state remain unambiguous.

When several items become eligible simultaneously, the dispatcher queues them while enforcing the five-second restriction for each channel.

Queue ordering should be deterministic. A recommended ordering is:

1. notification level, highest first;
2. scheduled notification time, oldest first;
3. stable reminder identifier as a tie-breaker.

In the simple mode all items are `LOW`, so oldest due time is normally sufficient.

---

## 13. Persistence and Home Assistant restart behavior

Reminder scheduling state must survive:

- Home Assistant restart;
- integration reload;
- integration update;
- temporary entity unavailability.

Internal state should be stored using Home Assistant's supported storage mechanism, such as `.storage`, rather than creating entities for every simple item.

On startup or reload, the integration reconciles persisted state with each managed `todo.*` entity:

- known pending item: restore its cycle;
- unknown pending item: create reminder state;
- persisted item no longer present: remove reminder state;
- completed item: cancel and clean its active state;
- item changed while the integration was offline: treat it as edited and restart;
- execution that became due while Home Assistant was offline: make it eligible as soon as possible, subject to quiet hours and channel queueing.

The integration must avoid duplicate notification immediately after restart. It should persist delivery timestamps and use idempotent scheduling guards so a recent successful delivery is not repeated solely because Home Assistant restarted.

All persisted timestamps must be timezone-aware. Internal storage should use UTC; UI and scheduling calculations must respect the Home Assistant configured timezone, including daylight-saving transitions.

---

## 14. Entities created for each person

### 14.1 To-do entity

```text
todo.reminders_<person_name>
```

Examples:

```text
todo.reminders_igor
todo.reminders_jade
```

The state follows Home Assistant to-do semantics and represents the number of incomplete items.

### 14.2 Pending reminders sensor

```text
sensor.<person_name>_pending_reminders
```

The state is the number of incomplete reminder items for that person.

### 14.3 Next reminder sensor

```text
sensor.<person_name>_next_reminder
```

The state is the next planned attempt timestamp for that person, considering:

- item due date/time;
- progressive interval;
- delivery retries;
- quiet hours;
- queued work and the five-second channel window where practical.

Recommended attributes:

```yaml
reminder_id: "01JEXAMPLE"
title: "Buy pet food"
reason: "progressive_interval"
```

When there is no future pending reminder, the sensor should use an appropriate Home Assistant empty state such as `unknown`, with attributes cleared.

### 14.4 No person-wide enable switch

The simple-mode person device does not include a global enable/disable switch. Silencing all reminders for a person could accidentally hide important pending tasks.

Enable/disable behavior is reserved for individual advanced reminder devices.

### 14.5 No events in the MVP

Custom events such as delivered, failed or completed are intentionally excluded from the initial version. They may be added later if a concrete automation use case emerges.

---

## 15. Configuration flows

The integration must use Home Assistant UI configuration flows and options flows. YAML configuration should not be required for the integration itself.

### 15.1 Initial setup

Recommended flow:

1. Add the integration.
2. Select an existing `person.*` entity.
3. Configure progressive intervals, prefilled with `15m, 30m, 1h, 4h`.
4. Configure quiet hours.
5. Configure morning, afternoon and evening reference times.
6. Configure delivery retry interval and maximum short retries, with defaults.
7. Finish creation of the person configuration device and its entities.

People should be selected explicitly rather than importing every `person.*` entity automatically. Additional people can be added through the integration UI.

### 15.2 Channel management

The integration must provide UI actions to:

- add a channel by selecting a `script.*` entity;
- give the channel a friendly name;
- enable or disable it;
- edit it;
- remove it when safe;
- assign it to one or more configured people;
- define its priority independently for every assigned person.

A person configuration may be saved without channels, but the integration should surface a configuration warning because no reminder can be delivered.

### 15.3 Person options

The user must be able to modify:

- progressive intervals;
- quiet hours;
- delivery retry settings;
- channel assignments and priorities.

Updating intervals must recalculate future schedules safely. It must not cause an immediate duplicate delivery for an item that was just notified.

---

## 16. Diagnostics and logging

The MVP exposes diagnostic sensors but no custom events.

Logs should provide enough information to diagnose delivery without exposing sensitive message contents unnecessarily.

Recommended log cases:

- new to-do item detected;
- item edited and cycle restarted;
- item completed or removed;
- notification suppressed by quiet hours;
- channel queued by the five-second rule;
- channel started;
- channel returned failure and its optional reason;
- invalid channel response;
- channel timeout or execution exception;
- fallback to another channel;
- all channels failed;
- state restored after restart.

Diagnostics downloads should redact reminder titles, descriptions and other personal content by default, while preserving identifiers, timestamps, states and failure categories needed for troubleshooting.

---

## 16.1 Finalized simple-mode edge cases

The following rules are definitive for the MVP:

- A `LOW` item whose due time falls inside quiet hours becomes eligible immediately when quiet hours end. After successful delivery, its progressive sequence continues normally.
- `pending -> completed` is completion, not a generic edit. `completed -> pending` is reopening. Both use their dedicated lifecycle rules.
- If an item is edited while old work is queued, the old generation is invalidated. Queued work and late responses from the old generation cannot send or reschedule the stale version.
- Removing a configured channel does not remove reminders. Remaining channels continue to be used. If it was the only configured channel, reminders remain pending.
- A person configuration may exist without channels. This is a configuration-incomplete state rather than a delivery failure. No short-delivery retry counters advance while no channel is configured. When a channel becomes available/configured, overdue reminders become eligible again.
- A configured script that temporarily reports `unavailable` is skipped for that attempt. If all configured channels are temporarily unavailable, the attempt is a normal complete delivery failure and follows the retry policy.
- If a referenced script has been removed from Home Assistant, its channel association becomes invalid and the integration exposes a configuration warning until corrected or removed.
- Equal-priority channels use round-robin selection. If the selected channel fails, the other channels in that priority group are tried before moving to the next priority. Round-robin position does not need to survive a Home Assistant restart.
- Only real delivery attempts count toward delivery retry counters. Waiting for throttling, quiet hours, or missing channel configuration does not.

### 16.2 Removing a person configuration

Removing a person configuration is allowed even when pending items exist, but the UI must require explicit confirmation and clearly state that the associated reminder list, pending items and integration-owned scheduling state will be deleted/cancelled.

## 17. Advanced mode — complex reminder devices

### 17.1 Creation and device model

Advanced reminders are created through the integration UI. Each reminder is represented by a permanent logical Home Assistant device. The device configuration is persistent while individual reminder occurrences are internal runtime objects and do not create one entity per occurrence.

Initial entities:

```text
Device: Check car oil
├── switch.check_car_oil
├── sensor.check_car_oil_next_occurrence
└── sensor.check_car_oil_status
```

The initial advanced-mode implementation intentionally exposes only these entities. Additional entities may be introduced later when a concrete use case requires them.

### 17.2 Recipients and delivery state

A reminder can target one or more configured people. The reminder occurrence is shared, but **delivery state is independent per recipient**. Each recipient maintains their own progressive notification cycle, delivery retries, next attempt and channel fallback using that person's channel assignments.

Completion is global: when any recipient completes the occurrence, it is completed for every recipient and all remaining queued or future deliveries are cancelled.

Notification level belongs to the reminder device and is the same for every recipient. Supported levels are `LOW`, `NORMAL`, `HIGH` and `CRITICAL`. `HIGH` and `CRITICAL` ignore quiet hours.

### 17.3 Occurrences

A scheduled execution creates one logical occurrence. Occurrences have stable internal identifiers and a generation/version so stale queued work or late script responses cannot affect a newer occurrence.

Only one active occurrence exists for a reminder at a time. For normal end-of-day reminders, a later occurrence replaces an unfinished earlier occurrence. For reminders configured to remain active until completion, a new recurrence does not replace or duplicate the still-active occurrence.

### 17.4 Completion policy

Every advanced reminder defines a completion policy:

```text
EXPIRE_AT_END_OF_DAY
UNTIL_COMPLETED
```

`EXPIRE_AT_END_OF_DAY` keeps the occurrence active until it is completed or the local calendar date of that occurrence ends. At the end of the date, an unfinished occurrence expires.

`UNTIL_COMPLETED` never expires merely because the date changed. Notification attempts continue across days until a completion is received, while still respecting quiet hours for `LOW` and `NORMAL`. This mode is intended for reminders that must not be lost, such as checking or changing vehicle oil.

### 17.5 Recurrence reference

Recurring reminders define how their next recurrence is calculated:

```text
SCHEDULE
COMPLETION
```

`SCHEDULE` keeps the original recurrence calendar anchored to the reminder's configured start date/time. Delayed completion does not move later recurrence dates.

`COMPLETION` calculates the next recurrence from the time the active occurrence is completed. Example: a reminder every 60 days that becomes active on September 1 but is completed on September 20 will next occur 60 days after September 20.

`COMPLETION` is valid only with `UNTIL_COMPLETED`. The configuration UI must reject `EXPIRE_AT_END_OF_DAY + COMPLETION`, because an expired occurrence may have no completion timestamp from which to calculate the next recurrence.

For `UNTIL_COMPLETED + SCHEDULE`, if another scheduled recurrence arrives while an occurrence remains active, no second occurrence is created. After completion, the scheduler selects the next future recurrence from the original calendar.

### 17.6 Scheduling

Advanced reminders support at least:

- one-time date/time;
- daily recurrence;
- weekly recurrence;
- selected weekdays;
- every X days;
- exact time;
- morning;
- afternoon;
- evening.

A schedule must resolve to a concrete local execution time. Morning, afternoon and evening are fixed at **09:00**, **13:00**, and **18:00**. A recurrence without an exact time must therefore select one of these periods.

`every X days` is initially anchored to the moment/date the reminder is configured. With `SCHEDULE`, later occurrences remain anchored to that calendar. With `COMPLETION`, completion becomes the anchor for the following interval.

All scheduling uses the Home Assistant configured timezone and must correctly handle date changes and daylight-saving transitions.

### 17.7 Notification cycle

Advanced reminders reuse the same delivery engine as simple reminders. Progressive intervals and retry configuration come from each recipient's person configuration rather than from the reminder device. Channel priority, fallback, five-second channel protection, fixed five-second script timeout, quiet hours and delivery response validation therefore behave consistently in both modes.

Each recipient advances their progressive sequence only after successful delivery to one of their channels. Completion of the shared occurrence cancels all recipient cycles.

### 17.8 Enable and disable

Every advanced reminder exposes an enable switch.

When disabled:

- the active occurrence is cancelled, not paused;
- queued and scheduled executions are cancelled;
- configuration is preserved;
- missed occurrences do not accumulate.

When re-enabled, the scheduler calculates the next future occurrence. Nothing missed while disabled is sent retroactively.

### 17.9 Editing

Editing an advanced reminder invalidates its current generation and restarts its scheduling state. Active occurrences, retries and queued deliveries from the previous configuration are cancelled. Late responses from the previous generation are ignored. The next occurrence is calculated from the updated configuration.

This intentionally favors predictable behavior over trying to preserve partially executed state across configuration changes.

### 17.10 Status and next occurrence

`sensor.<reminder>_status` uses the following conceptual states:

```text
scheduled
active
completed
expired
disabled
```

`expired` applies to an `EXPIRE_AT_END_OF_DAY` occurrence that reaches the end of its date without completion. `UNTIL_COMPLETED` occurrences remain `active` until completed.

`sensor.<reminder>_next_occurrence` represents the next recurrence according to the configured recurrence policy, even when a persistent occurrence is currently active. The `status` sensor communicates that the current occurrence still requires completion.

### 17.11 Completion action contract

Completion must be exposed through a generic HA Reminder action/service so the origin is independent of the reminder engine. Mobile actionable notifications, automations, scripts, voice flows, physical buttons or future UI controls can all call the same action.

The action contract must identify the reminder/active occurrence and the requested interaction. The initial required interaction is `COMPLETE`; the contract must reserve space for `SNOOZE`, `ACKNOWLEDGE` and `DISMISS`. A completion is idempotent: repeating completion for an already-finished or stale occurrence must not create new scheduling effects.

## 18. Future interaction actions

The architecture should keep room for mobile actionable notifications, although only completion through the to-do item lifecycle is required now.

Potential future actions:

```text
COMPLETE
SNOOZE
ACKNOWLEDGE
DISMISS
```

These meanings must remain distinct:

- **Complete:** the task was performed and notification cycles stop.
- **Snooze:** schedule another attempt after a selected delay.
- **Acknowledge:** the user confirms seeing the reminder; future semantics still need definition.
- **Dismiss:** the notification surface was dismissed and does not necessarily mean completion.

The generic channel result must not be confused with any of these user actions.

---

## 19. Non-functional requirements

### 19.1 Local-first operation

The core integration should operate locally inside Home Assistant. External services may be used by user-defined channel scripts but are not required by the reminder engine.

### 19.2 Asynchronous execution

All scheduling, storage and script calls must use Home Assistant's asynchronous patterns. The event loop must not be blocked.

### 19.3 Concurrency safety

The implementation must prevent:

- duplicate delivery caused by concurrent schedulers;
- two invocations of the same channel within five seconds;
- stale queued items being sent after completion;
- sequence advancement from late responses belonging to cancelled or restarted item generations.

An internal generation/version number per reminder cycle is recommended. Editing, reopening or restarting an item increments the generation so stale asynchronous results can be ignored.

### 19.4 Stable identifiers

Device and entity unique IDs must not depend only on mutable friendly names. They should use stable integration-owned identifiers and the associated person identifier.

### 19.5 Availability

Temporary unavailability of the `person.*`, `todo.*` or channel `script.*` entity must not delete configuration or reminder state.

---

## 20. MVP scope

### Included

- UI-based integration setup.
- Explicit selection of people.
- Logical configuration device per person.
- Dedicated local `todo.*` entity per person.
- Independent tracking of every pending item.
- Low notification level for simple items.
- Creation-time scheduling using the first person interval.
- Due-date/time scheduling.
- Progressive per-person intervals.
- Per-person quiet hours.
- Script-only notification channels.
- Shared channels with per-person priority.
- Duplicate channel priorities as alternatives.
- Fallback until the first successful channel.
- Standard script input and response contract.
- Channel timeout and response validation.
- Five-second global protection per channel.
- Short delivery retries after complete channel failure.
- Completion, removal, editing and reopening lifecycle handling.
- Persistent state and restart reconciliation.
- Pending-count and next-reminder sensors.
- No person-wide enable switch.

### Excluded from the initial simple-mode MVP

- One device per simple to-do item.
- Grouping several items into one notification.
- Custom integration events.
- Person-presence filtering inside the reminder engine.
- Native knowledge of mobile, TV, Alexa or other destination types.
- Advanced recurrence rules.
- Advanced reminder devices.
- User acknowledgement tracking.
- Snooze handling.
- Notification history UI.
- Custom frontend panel.

---

## 21. Finalized product decisions

The following decisions are finalized for the current specification:

1. Integration name: **HA Reminder**.
2. Integration domain: `ha_reminder`.
3. Date-only simple to-do items execute at **09:00** on their due date.
4. Fixed period times are Morning **09:00**, Afternoon **13:00**, Evening **18:00**.
5. Removing a person with pending items is allowed only after explicit destructive confirmation.
6. Equal-priority channels use round-robin; the cursor does not require persistence across restart.
7. Channel execution timeout is fixed at **5 seconds**.
8. Missing channel configuration is not a delivery failure; temporary unavailability of all configured channels is.
9. Advanced reminders support explicit completion policies and recurrence references as defined in Section 17.
10. Detailed presentation/layout of config-flow screens and internal implementation structure may be chosen freely as long as all behavioral requirements and Home Assistant conventions in this document are preserved.

## 22. Acceptance examples

### 22.1 Simple item delivered on preferred channel

Given:

- Igor has intervals `15m, 30m, 1h, 4h`;
- Mobile is priority 1;
- TV is priority 2;
- an item is created at 09:00 without a due time.

Expected:

- no notification at 09:00;
- at 09:15 Mobile is called;
- Mobile returns `success: true`;
- TV is not called;
- next notification is scheduled for 09:45;
- completing the item before 09:45 cancels the next notification.

### 22.2 Fallback to TV

Given the same configuration:

- at 09:15 Mobile returns `success: false`;
- TV returns `success: true`.

Expected:

- the delivery cycle is successful;
- the sequence advances;
- next notification is scheduled using the next progressive interval;
- Mobile remains the first candidate in the following cycle.

### 22.3 Complete channel failure

Given all assigned channels fail at 09:15:

Expected:

- the progressive sequence does not advance;
- a delivery retry is scheduled for 09:20;
- after three short failures, the short retry counter resets;
- another attempt is scheduled using the person's first interval;
- the reminder remains pending.

### 22.4 Quiet hours

Given:

- Igor's quiet hours are 22:00–07:00;
- a `LOW` reminder becomes eligible at 23:00.

Expected:

- no channel is called at 23:00;
- the sequence does not advance;
- the item becomes eligible when quiet hours end at 07:00;
- queueing still observes the five-second channel rule.

### 22.5 Shared channel throttling

Given:

- a TV channel is shared by Igor and Jade;
- both have a reminder routed to the TV at the same time.

Expected:

- the first invocation starts immediately;
- the second waits until at least five seconds after the first channel invocation;
- waiting is not treated as channel failure;
- no fallback occurs solely because of that wait.

### 22.6 Edited item

Given an item has already reached the one-hour stage and its title or due time is changed:

Expected:

- its current cycle is invalidated;
- short retry and delivery counters reset;
- it is treated as new;
- stale responses from the old cycle cannot schedule future notifications.

### 22.7 Restart recovery

Given Home Assistant restarts after a successful delivery and before the next interval:

Expected:

- the integration restores the item state;
- it does not duplicate the recent notification;
- it preserves the next planned notification;
- completing the item after restart cancels the restored schedule.

