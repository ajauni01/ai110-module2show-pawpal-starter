import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet


def test_task_completion():
    task = Task(
        task_id="t1",
        title="Morning walk",
        duration_minutes=30,
        priority="high",
        frequency="daily",
    )
    assert task.is_completed is False
    task.complete()
    assert task.is_completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog", age=3)
    assert len(pet.tasks) == 0

    pet.add_task(Task(
        task_id="t1",
        title="Feed breakfast",
        duration_minutes=10,
        priority="high",
        frequency="daily",
    ))
    assert len(pet.tasks) == 1

    pet.add_task(Task(
        task_id="t2",
        title="Grooming brush",
        duration_minutes=15,
        priority="medium",
        frequency="weekly",
    ))
    assert len(pet.tasks) == 2
