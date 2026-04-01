from dataclasses import dataclass


@dataclass
class Pet:
    name: str
    species: str  # "dog", "cat", "other"
    age: int = 0
    notes: str = ""


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    is_required: bool = False
    task_id: str = ""


class Owner:
    def __init__(self, name: str, available_minutes: int, pet: Pet):
        self.name = name
        self.available_minutes = available_minutes
        self.pet = pet
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task_id: str) -> None:
        pass


class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner

    def generate_plan(self) -> dict:
        pass

    def _rank_tasks(self) -> list[Task]:
        pass
