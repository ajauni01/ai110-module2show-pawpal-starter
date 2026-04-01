from dataclasses import dataclass


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str           # "low", "medium", "high"
    frequency: str          # "daily", "weekly", "as_needed"
    is_completed: bool = False
    task_id: str = ""

    def complete(self) -> None:
        """Mark this task as completed."""
        self.is_completed = True

    def reset(self) -> None:
        """Reset this task to incomplete."""
        self.is_completed = False

    def __str__(self) -> str:
        """Return a human-readable summary of the task."""
        status = "done" if self.is_completed else "pending"
        return f"[{self.priority.upper()}] {self.title} ({self.duration_minutes} min, {self.frequency}) — {status}"


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

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return all tasks across all pets as (pet, task) pairs."""
        result = []
        for pet in self.pets:
            for task in pet.tasks:
                result.append((pet, task))
        return result

    def __str__(self) -> str:
        """Return a human-readable summary of the owner."""
        return f"{self.name} ({len(self.pets)} pet(s), {self.available_minutes} min available)"


class Scheduler:
    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, owner: Owner):
        self.owner = owner

    def _rank_tasks(self) -> list[tuple[Pet, Task]]:
        """Sort all pending tasks by priority (high first), then by duration (shortest first)."""
        all_tasks = self.owner.get_all_tasks()
        pending = [(pet, task) for pet, task in all_tasks if not task.is_completed]
        return sorted(
            pending,
            key=lambda x: (self.PRIORITY_ORDER.get(x[1].priority, 2), x[1].duration_minutes)
        )

    def generate_plan(self) -> dict:
        """
        Greedily builds a daily plan that fits within the owner's available time.
        Required high-priority tasks are always included first.
        Returns a dict with scheduled, skipped, total_duration, and explanation.
        """
        ranked = self._rank_tasks()
        scheduled = []
        skipped = []
        time_remaining = self.owner.available_minutes
        explanation = []

        for pet, task in ranked:
            if task.duration_minutes <= time_remaining:
                scheduled.append((pet, task))
                time_remaining -= task.duration_minutes
                explanation.append(
                    f"✓ '{task.title}' for {pet.name} scheduled "
                    f"({task.duration_minutes} min, {task.priority} priority)"
                )
            else:
                skipped.append((pet, task))
                explanation.append(
                    f"✗ '{task.title}' for {pet.name} skipped "
                    f"(needs {task.duration_minutes} min, only {time_remaining} min left)"
                )

        total_duration = self.owner.available_minutes - time_remaining

        return {
            "scheduled": scheduled,
            "skipped": skipped,
            "total_duration": total_duration,
            "time_remaining": time_remaining,
            "explanation": explanation,
        }

    def explain_plan(self) -> str:
        """Return a formatted string explaining the generated daily plan."""
        plan = self.generate_plan()
        lines = [f"Daily plan for {self.owner.name}:", ""]
        lines += plan["explanation"]
        lines += [
            "",
            f"Total time used: {plan['total_duration']} / {self.owner.available_minutes} min",
            f"Tasks scheduled: {len(plan['scheduled'])}",
            f"Tasks skipped:   {len(plan['skipped'])}",
        ]
        return "\n".join(lines)
