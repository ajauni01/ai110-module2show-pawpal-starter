from dataclasses import dataclass, field
from datetime import date


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str           # "low", "medium", "high"
    frequency: str          # "daily", "weekly", "as_needed"
    is_completed: bool = False
    task_id: str = ""
    preferred_time: str = "any"          # "morning", "afternoon", "evening", "any"
    last_completed_date: str = ""        # ISO date string, e.g. "2026-04-01"
    start_time: str = ""                 # "HH:MM" format, e.g. "08:30"

    # Internal sort order for preferred_time slots
    _TIME_ORDER: dict = field(default_factory=lambda: {
        "morning": 0, "afternoon": 1, "evening": 2, "any": 3
    }, init=False, repr=False, compare=False)

    def complete(self) -> None:
        """Mark this task as completed and record today's date."""
        self.is_completed = True
        self.last_completed_date = date.today().isoformat()

    def reset(self) -> None:
        """Reset this task to incomplete."""
        self.is_completed = False

    def is_due_today(self) -> bool:
        """
        Recurring-task logic:
        - daily / as_needed tasks are always due.
        - weekly tasks are skipped if already completed within the last 7 days.
        """
        if self.frequency != "weekly":
            return True
        if not self.last_completed_date:
            return True
        days_since = (date.today() - date.fromisoformat(self.last_completed_date)).days
        return days_since >= 7

    def time_order(self) -> int:
        """Return a numeric sort key for preferred_time."""
        return {"morning": 0, "afternoon": 1, "evening": 2, "any": 3}.get(
            self.preferred_time, 3
        )

    def __str__(self) -> str:
        """Return a human-readable summary of the task."""
        status = "done" if self.is_completed else "pending"
        return (
            f"[{self.priority.upper()}] {self.title} "
            f"({self.duration_minutes} min, {self.frequency}, {self.preferred_time}) — {status}"
        )


class Pet:
    def __init__(self, name: str, species: str, age: int = 0, notes: str = ""):
        self.name = name
        self.species = species
        self.age = age
        self.notes = notes
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a task from this pet's task list by task_id."""
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def get_pending_tasks(self) -> list[Task]:
        """Return all incomplete tasks for this pet."""
        return [t for t in self.tasks if not t.is_completed]

    def __str__(self) -> str:
        """Return a human-readable summary of the pet."""
        return f"{self.name} ({self.species}, age {self.age})"


class Owner:
    def __init__(self, name: str, available_minutes: int):
        self.name = name
        self.available_minutes = available_minutes
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's pet list."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """Remove a pet from this owner's pet list by name."""
        self.pets = [p for p in self.pets if p.name != pet_name]

    def get_all_tasks(self) -> list[tuple["Pet", Task]]:
        """Return all tasks across all pets as (pet, task) pairs."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def get_tasks_for_pet(self, pet_name: str) -> list[tuple["Pet", Task]]:
        """Filter tasks to only those belonging to a specific pet."""
        return [
            (pet, task)
            for pet, task in self.get_all_tasks()
            if pet.name == pet_name
        ]

    def get_tasks_by_status(self, completed: bool) -> list[tuple["Pet", Task]]:
        """Filter all tasks by completion status."""
        return [
            (pet, task)
            for pet, task in self.get_all_tasks()
            if task.is_completed == completed
        ]

    def __str__(self) -> str:
        """Return a human-readable summary of the owner."""
        return f"{self.name} ({len(self.pets)} pet(s), {self.available_minutes} min available)"


class Scheduler:
    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, owner: Owner):
        self.owner = owner

    def _rank_tasks(self) -> list[tuple[Pet, Task]]:
        """
        Build an ordered list of tasks eligible to be scheduled today.

        A task is eligible when it is not yet completed AND is due today
        (see Task.is_due_today for the recurrence logic).  Eligible tasks
        are then sorted by three keys in order of importance:

          1. Priority    — high (0) → medium (1) → low (2)
          2. Time slot   — morning (0) → afternoon (1) → evening (2) → any (3)
          3. Duration    — shortest first, as a tiebreaker within the same
                          priority and slot so the greedy planner can fit more
                          tasks inside the available-minutes budget.

        Returns:
            A sorted list of (Pet, Task) tuples ready for the greedy planner.
        """
        all_tasks = self.owner.get_all_tasks()
        eligible = [
            (pet, task)
            for pet, task in all_tasks
            if not task.is_completed and task.is_due_today()
        ]
        return sorted(
            eligible,
            key=lambda x: (
                self.PRIORITY_ORDER.get(x[1].priority, 2),
                x[1].time_order(),
                x[1].duration_minutes,
            ),
        )

    @staticmethod
    def _to_minutes(hhmm: str) -> int:
        """
        Convert a zero-padded 24-hour time string to minutes since midnight.

        This helper keeps the overlap arithmetic in detect_conflicts readable
        by working entirely in integer minutes rather than datetime objects.

        Args:
            hhmm: A string in "HH:MM" format, e.g. "07:30" or "18:05".

        Returns:
            Total minutes since midnight (e.g. "07:30" → 450).
        """
        h, m = hhmm.split(":")
        return int(h) * 60 + int(m)

    def detect_conflicts(self) -> list[str]:
        """
        Lightweight conflict detection based on exact time-window overlap.

        Two tasks conflict when their scheduled windows overlap:
            start_A < end_B  AND  start_B < end_A

        Only tasks that have a start_time set are checked — tasks without one
        are silently skipped so the program never crashes.
        Returns a list of human-readable warning strings (one per conflict pair).
        """
        timed = [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if task.start_time  # skip tasks with no start_time
        ]

        warnings = []
        # Compare every unique pair (i, j) where i < j
        for i in range(len(timed)):
            for j in range(i + 1, len(timed)):
                pet_a, task_a = timed[i]
                pet_b, task_b = timed[j]

                start_a = self._to_minutes(task_a.start_time)
                end_a   = start_a + task_a.duration_minutes
                start_b = self._to_minutes(task_b.start_time)
                end_b   = start_b + task_b.duration_minutes

                if start_a < end_b and start_b < end_a:
                    end_a_str = f"{end_a // 60:02d}:{end_a % 60:02d}"
                    end_b_str = f"{end_b // 60:02d}:{end_b % 60:02d}"
                    warnings.append(
                        f"⚠ Conflict: '{task_a.title}' ({pet_a.name}, "
                        f"{task_a.start_time}–{end_a_str}) overlaps with "
                        f"'{task_b.title}' ({pet_b.name}, "
                        f"{task_b.start_time}–{end_b_str})"
                    )
        return warnings

    def sort_by_time(self) -> list[tuple[Pet, Task]]:
        """
        Return all owner tasks sorted chronologically by start_time.

        The sort key is a lambda that produces a (missing, hhmm) tuple:
          - missing is True (1) when start_time is empty, False (0) otherwise,
            so un-timed tasks always fall to the end of the list.
          - hhmm is the raw "HH:MM" string; lexicographic comparison works
            correctly for zero-padded 24-hour times without parsing.

        Returns:
            All (Pet, Task) pairs in ascending start_time order.
            Tasks with no start_time appear last, in their original order.
        """
        all_tasks = self.owner.get_all_tasks()
        return sorted(
            all_tasks,
            key=lambda x: (x[1].start_time == "", x[1].start_time)
        )

    def filter_tasks(
        self,
        pet_name: str | None = None,
        completed: bool | None = None,
    ) -> list[tuple[Pet, Task]]:
        """
        Return a filtered view of all owner tasks.

        Each filter is optional and independent; when both are provided they
        are applied together (AND logic).

        Args:
            pet_name:  If given, only tasks belonging to the pet with this
                       name are returned.  Case-sensitive.
            completed: If True, return only completed tasks.
                       If False, return only pending tasks.
                       If None (default), completion status is not filtered.

        Returns:
            A list of (Pet, Task) tuples matching all supplied filters.

        Examples:
            scheduler.filter_tasks(pet_name="Mochi")
                → all of Mochi's tasks regardless of status

            scheduler.filter_tasks(completed=False)
                → every pending task across all pets

            scheduler.filter_tasks(pet_name="Luna", completed=True)
                → only Luna's completed tasks
        """
        results = self.owner.get_all_tasks()
        if pet_name is not None:
            results = [(p, t) for p, t in results if p.name == pet_name]
        if completed is not None:
            results = [(p, t) for p, t in results if t.is_completed == completed]
        return results

    def generate_plan(self) -> dict:
        """
        Greedily builds a daily plan that fits within the owner's available time.
        Respects priority, preferred time slot, and recurring-task due dates.
        Returns a dict with scheduled, skipped, total_duration, conflicts, and explanation.
        """
        ranked = self._rank_tasks()
        scheduled = []
        skipped = []
        not_due = [
            (pet, task)
            for pet, task in self.owner.get_all_tasks()
            if not task.is_completed and not task.is_due_today()
        ]
        time_remaining = self.owner.available_minutes
        explanation = []

        for pet, task in ranked:
            if task.duration_minutes <= time_remaining:
                scheduled.append((pet, task))
                time_remaining -= task.duration_minutes
                explanation.append(
                    f"✓ '{task.title}' for {pet.name} scheduled "
                    f"({task.duration_minutes} min, {task.priority}, {task.preferred_time})"
                )
            else:
                skipped.append((pet, task))
                explanation.append(
                    f"✗ '{task.title}' for {pet.name} skipped "
                    f"(needs {task.duration_minutes} min, only {time_remaining} min left)"
                )

        for pet, task in not_due:
            explanation.append(
                f"— '{task.title}' for {pet.name} skipped (weekly, not due yet)"
            )

        total_duration = self.owner.available_minutes - time_remaining

        return {
            "scheduled": scheduled,
            "skipped": skipped,
            "not_due": not_due,
            "total_duration": total_duration,
            "time_remaining": time_remaining,
            "conflicts": self.detect_conflicts(),
            "explanation": explanation,
        }

    def explain_plan(self) -> str:
        """Return a formatted string explaining the generated daily plan."""
        plan = self.generate_plan()
        lines = [f"Daily plan for {self.owner.name}:", ""]

        if plan["conflicts"]:
            lines += ["CONFLICTS DETECTED:"] + plan["conflicts"] + [""]

        lines += plan["explanation"]
        lines += [
            "",
            f"Total time used: {plan['total_duration']} / {self.owner.available_minutes} min",
            f"Tasks scheduled: {len(plan['scheduled'])}",
            f"Tasks skipped:   {len(plan['skipped'])}",
            f"Not due today:   {len(plan['not_due'])}",
        ]
        return "\n".join(lines)
