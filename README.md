# PawPal+ (Module 2 Project)

PawPal+ is a **Streamlit app** that helps a busy pet owner plan daily care tasks across multiple pets — automatically sorted, conflict-checked, and time-budgeted.

## Features

- **Priority-aware scheduling** — high-priority tasks (medications, feeding) are always placed before medium and low ones in the daily plan.
- **Greedy time-budget planner** — tasks are added to the daily plan greedily until `available_minutes` is exhausted; tasks that don't fit are listed separately so nothing is silently dropped.
- **Sorting by time-of-day** — tasks with a `start_time` are displayed in chronological order; tasks without one are pushed to the end.
- **Flexible filtering** — view tasks by pet name, completion status, or both at once using `Scheduler.filter_tasks()`.
- **Conflict warnings** — two tasks that overlap in clock time (i.e. `start_A < end_B AND start_B < end_A`) trigger a visible `st.warning` banner before the day starts.
- **Daily recurrence logic** — weekly tasks that were completed within the last 7 days are automatically excluded from today's plan; the exact 7-day boundary is respected.
- **Plan explanation** — an expandable section shows the reasoning behind every scheduling decision (scheduled, skipped, or not due).

## Demo

<!-- Replace the path below with your actual screenshot filename after running the app -->
<a href="/course_images/ai110/pawpal_demo.png" target="_blank"><img src="/course_images/ai110/pawpal_demo.png" alt="PawPal+ demo screenshot" width="700"></a>

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Smarter Scheduling

The `Scheduler` class (in `pawpal_system.py`) goes beyond a simple priority queue.
Four algorithmic improvements make the daily plan more useful:

### 1. Time-of-day sorting — `sort_by_time()`
Tasks can be assigned a `start_time` in `"HH:MM"` format.
`sort_by_time()` uses a lambda sort key on the raw string:

```python
key=lambda x: (x[1].start_time == "", x[1].start_time)
```

Zero-padded 24-hour strings sort lexicographically in the correct order, so
no datetime parsing is needed.  Tasks without a `start_time` are pushed to
the end of the list.

### 2. Flexible filtering — `filter_tasks(pet_name, completed)`
`filter_tasks()` accepts two independent, optional parameters:

| Call | Returns |
|---|---|
| `filter_tasks(pet_name="Mochi")` | All of Mochi's tasks |
| `filter_tasks(completed=False)` | Every pending task across all pets |
| `filter_tasks(pet_name="Luna", completed=True)` | Only Luna's completed tasks |

Both filters are applied with AND logic when combined.

### 3. Recurring-task awareness — `Task.is_due_today()`
The `frequency` field is now enforced by the scheduler.
- `"daily"` and `"as_needed"` tasks are always eligible.
- `"weekly"` tasks are skipped if `last_completed_date` is within the last
  7 days, preventing redundant work from appearing in the daily plan.

### 4. Conflict detection — `detect_conflicts()`
Uses the standard interval-overlap condition to find scheduling collisions:

```
conflict  ⟺  start_A < end_B  AND  start_B < end_A
```

Every pair of timed tasks is compared.  The method returns a list of
human-readable warning strings — one per conflict — and never raises an
exception.  Tasks without a `start_time` are silently skipped.

## Testing PawPal+

Run the full test suite from the project root:

```bash
python3 -m pytest tests/test_pawpal.py -v
```

### What the tests cover

| Group | Tests | What is verified |
|---|---|---|
| **Sorting** | `test_sort_by_time_*`, `test_rank_tasks_priority_order` | Tasks added out of order come back in correct chronological / priority order; untimed tasks sort last |
| **Recurrence** | `test_daily_task_*`, `test_weekly_task_*` | Daily tasks are always due; weekly tasks respect the 7-day cooldown boundary; not-due tasks are excluded from the plan |
| **Conflict detection** | `test_conflict_detected_*`, `test_no_conflict_*` | Overlapping windows are flagged; back-to-back (adjacent) tasks are not; tasks with no `start_time` never trigger false positives |
| **Edge cases** | `test_pet_with_no_tasks_*`, `test_all_tasks_exceed_budget_*`, etc. | Empty pets/owners, full budget exhaustion, pre-completed tasks, and unmatched filter names all behave gracefully |

**Confidence level: ★★★★☆**
Core scheduling logic (priority ordering, recurrence gating, conflict detection) is fully covered.
One star withheld because the Streamlit UI layer (`app.py`) has no automated tests — those paths rely on manual verification.
