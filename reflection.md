# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The initial UML included four classes with clear, separated responsibilities:

- **`Task`** — a data container holding everything about a single care item: title, duration, priority, frequency, and completion state. No scheduling logic lives here; it only knows about itself.
- **`Pet`** — owns a list of `Task` objects and exposes methods to add, remove, and query them. A pet has no awareness of the owner's time budget.
- **`Owner`** — holds a list of `Pet` objects and a single constraint: `available_minutes`. Acts as the top-level aggregator; provides `get_all_tasks()` so the scheduler has one place to ask for everything.
- **`Scheduler`** — the only class that makes decisions. It takes an `Owner`, reads tasks across all pets, and produces a daily plan. All scheduling logic is isolated here so the other classes stay simple and testable.

**b. Design changes**

Yes — two meaningful changes happened during implementation.

First, `Task` gained three new fields (`preferred_time`, `start_time`, `last_completed_date`) that were not in the original design. The initial design treated all tasks as interchangeable; once sorting and conflict detection were added it became clear that a task needed to carry its own time metadata rather than having the scheduler infer or guess it.

Second, the `Scheduler` originally had a single `generate_plan()` method. It was split into several focused helpers (`_rank_tasks`, `_to_minutes`, `detect_conflicts`, `sort_by_time`, `filter_tasks`) as each new feature was added. The split was necessary to keep each piece independently testable and to avoid a single method growing too large to reason about.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers four constraints in this order:

1. **Recurrence** — a weekly task that was completed within the last 7 days is removed from consideration entirely before any other logic runs. There is no point prioritizing a task that should not happen today.
2. **Completion status** — already-completed tasks are excluded so the plan only shows work that still needs to be done.
3. **Priority** — high-priority tasks are always placed before medium and low ones. This is the constraint most directly tied to the owner's welfare (a missed medication is worse than a missed grooming session).
4. **Time budget** — the greedy loop never schedules a task if it would exceed `available_minutes`. The owner's time is a hard ceiling, not a soft suggestion.

Priority was ranked above time-of-day preference because a high-priority evening task is still more important than a low-priority morning task, even if it is scheduled "out of order."

**b. Tradeoffs**

The scheduler uses a **greedy algorithm**: it picks the best available task at each step and never backtracks. This means it can miss a globally better plan. For example, if the budget is 30 minutes and the remaining tasks are a 25-minute high-priority task followed by a 10-minute medium task, the greedy planner schedules only the 25-minute task (5 minutes left, not enough for the 10-minute one) even though two lower-duration tasks might have fit instead.

This tradeoff is reasonable for a pet care app because the owner needs a fast, predictable answer. The optimal combinatorial solution (a knapsack algorithm) would be harder to explain to a non-technical user and slower to compute as the task list grows. A greedy plan that always picks the highest-priority task is transparent and trustworthy even if it is not mathematically perfect.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used throughout the project in three distinct ways:

- **Scaffolding boilerplate** — generating the initial dataclass fields, `__str__` methods, and list comprehensions so that the session could focus on design decisions rather than syntax.
- **Debugging logic** — when the conflict detection warning string had a formatting bug (the `start_time[:-2]` slice was incorrect), explaining the problem to the AI produced an immediate, correct fix.
- **Expanding scope incrementally** — asking "what edge cases should I test for a pet scheduler with sorting and recurring tasks?" produced a structured list that was used directly to write the test suite, covering cases that might otherwise have been overlooked (e.g., the exact 7-day boundary for weekly tasks).

The most useful prompt pattern was providing a concrete constraint ("return warnings, never crash") alongside the specific method name — this scoped the AI's response tightly enough to be immediately useful rather than generic.

**b. Judgment and verification**

When the AI first implemented `detect_conflicts`, it used the vague `preferred_time` slot buckets (morning/afternoon/evening) with a hardcoded 30-minute budget threshold. That approach was not accepted as-is because it would produce false positives (two high-priority morning tasks that are actually scheduled hours apart) and miss real conflicts (two tasks at exactly the same `start_time` in different slots).

The suggestion was evaluated by tracing through two concrete examples by hand: one where tasks were in the same slot but hours apart, and one where they had identical `start_times`. The slot-budget approach failed both. It was replaced with the interval-overlap condition (`start_A < end_B and start_B < end_A`) which was then verified with a dedicated test (`test_no_conflict_for_back_to_back_tasks`) to confirm the boundary case produced zero false positives.

---

## 4. Testing and Verification

**a. What you tested**

Twenty tests were written across four groups:

- **Sorting correctness** — tasks added in reverse time order must come out chronologically sorted; untimed tasks must appear last; priority ordering must be high → medium → low.
- **Recurrence logic** — daily tasks are always due; weekly tasks respect the 7-day cooldown; the boundary case (exactly 7 days ago) must return `True`; tasks with no completion date must always be due; not-due tasks must be excluded from the generated plan.
- **Conflict detection** — overlapping windows are flagged; same-start-time is flagged; adjacent (back-to-back) tasks are not flagged; tasks without a `start_time` never produce warnings.
- **Edge cases** — empty pet, empty owner, all tasks over budget, pre-completed task excluded from plan, filter returning an empty list for an unknown pet name.

These tests matter because the recurrence boundary (exactly 7 days) and the conflict adjacency boundary (back-to-back ≠ overlap) are both easy to get wrong by one unit — an off-by-one error in either would silently produce the wrong plan every time.

**b. Confidence**

Confidence level: **★★★★☆ (4/5)**

The core scheduling logic is well-covered. The one area of lower confidence is the Streamlit UI layer — `app.py` has no automated tests, so regressions there would only be caught by manual testing. Additionally, the greedy planner is not tested against all possible task orderings that could expose a suboptimal plan; only the most common priority scenarios are covered.

If more time were available, the next edge cases to test would be:
- An owner with two pets where the same task title appears on both (name collision in filter)
- A task whose `duration_minutes` exactly equals `available_minutes` (must be scheduled, not skipped)
- `sort_by_time` stability — when two tasks share the same `start_time`, their relative order should be consistent across runs

---

## 5. Reflection

**a. What went well**

The separation of concerns between `Task`, `Pet`, `Owner`, and `Scheduler` worked well throughout. Every time a new feature was added (recurring tasks, conflict detection, time sorting), it slotted into `Scheduler` or `Task` without requiring changes to the other classes. That stability made the iterative build-and-test cycle fast and low-risk.

**b. What you would improve**

The `Task` dataclass grew more fields than originally intended (`preferred_time`, `start_time`, `last_completed_date`). In a next iteration, the time-related fields would be extracted into a separate `Schedule` or `TimeWindow` dataclass that `Task` holds as a single optional attribute. This would keep `Task` focused on what a task *is* rather than mixing in when it happens.

Additionally, the greedy planner would be worth replacing with a simple knapsack approach for small task lists (under ~20 tasks), since the task counts in a real pet care app are small enough that the extra complexity is manageable and the results would be more satisfying to users.

**c. Key takeaway**

The most important thing learned was that **AI is most useful when you already understand the problem well enough to evaluate its output**. The first conflict detection implementation looked correct at a glance but failed on the back-to-back boundary case. Catching that required knowing what question to ask ("does adjacent mean conflicting?") and having a concrete test to verify the answer. AI accelerates writing; human judgment determines whether what was written is right.
