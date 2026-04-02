import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Owner, Pet, Scheduler, Task


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_owner(minutes: int = 120) -> Owner:
    return Owner(name="Jordan", available_minutes=minutes)


def make_pet(name: str = "Mochi") -> Pet:
    return Pet(name=name, species="dog", age=3)


def days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


# ── Existing tests (preserved) ────────────────────────────────────────────────

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
    pet = make_pet()
    assert len(pet.tasks) == 0
    pet.add_task(Task(task_id="t1", title="Feed breakfast",
                      duration_minutes=10, priority="high", frequency="daily"))
    assert len(pet.tasks) == 1
    pet.add_task(Task(task_id="t2", title="Grooming brush",
                      duration_minutes=15, priority="medium", frequency="weekly"))
    assert len(pet.tasks) == 2


# ── Sorting correctness ───────────────────────────────────────────────────────

def test_sort_by_time_returns_chronological_order():
    """Tasks added out of order must come out sorted by start_time ascending."""
    owner = make_owner()
    pet = make_pet()
    # Added in reverse order on purpose
    pet.add_task(Task(task_id="t3", title="Evening walk",
                      duration_minutes=20, priority="low", frequency="daily",
                      start_time="18:00"))
    pet.add_task(Task(task_id="t1", title="Morning walk",
                      duration_minutes=30, priority="high", frequency="daily",
                      start_time="07:30"))
    pet.add_task(Task(task_id="t2", title="Lunch feeding",
                      duration_minutes=10, priority="medium", frequency="daily",
                      start_time="12:00"))
    owner.add_pet(pet)

    sorted_tasks = Scheduler(owner).sort_by_time()
    times = [task.start_time for _, task in sorted_tasks]
    assert times == ["07:30", "12:00", "18:00"]


def test_sort_by_time_untimed_tasks_go_last():
    """Tasks without a start_time must appear after all timed tasks."""
    owner = make_owner()
    pet = make_pet()
    pet.add_task(Task(task_id="t1", title="No-time task",
                      duration_minutes=10, priority="high", frequency="daily",
                      start_time=""))
    pet.add_task(Task(task_id="t2", title="Morning walk",
                      duration_minutes=30, priority="high", frequency="daily",
                      start_time="08:00"))
    owner.add_pet(pet)

    sorted_tasks = Scheduler(owner).sort_by_time()
    titles = [task.title for _, task in sorted_tasks]
    assert titles[-1] == "No-time task"


def test_rank_tasks_priority_order():
    """_rank_tasks must return high before medium before low priority."""
    owner = make_owner()
    pet = make_pet()
    pet.add_task(Task(task_id="t1", title="Low task",
                      duration_minutes=10, priority="low", frequency="daily"))
    pet.add_task(Task(task_id="t2", title="High task",
                      duration_minutes=10, priority="high", frequency="daily"))
    pet.add_task(Task(task_id="t3", title="Medium task",
                      duration_minutes=10, priority="medium", frequency="daily"))
    owner.add_pet(pet)

    ranked = Scheduler(owner)._rank_tasks()
    priorities = [task.priority for _, task in ranked]
    assert priorities == ["high", "medium", "low"]


# ── Recurrence logic ──────────────────────────────────────────────────────────

def test_daily_task_is_always_due():
    task = Task(task_id="t1", title="Walk", duration_minutes=20,
                priority="high", frequency="daily",
                last_completed_date=days_ago(0))   # completed today
    assert task.is_due_today() is True


def test_weekly_task_not_due_when_done_recently():
    """A weekly task completed 3 days ago must not be due."""
    task = Task(task_id="t1", title="Grooming", duration_minutes=15,
                priority="medium", frequency="weekly",
                last_completed_date=days_ago(3))
    assert task.is_due_today() is False


def test_weekly_task_due_when_done_7_days_ago():
    """A weekly task completed exactly 7 days ago must be due again."""
    task = Task(task_id="t1", title="Grooming", duration_minutes=15,
                priority="medium", frequency="weekly",
                last_completed_date=days_ago(7))
    assert task.is_due_today() is True


def test_weekly_task_due_when_never_completed():
    """A weekly task with no completion date must always be due."""
    task = Task(task_id="t1", title="Grooming", duration_minutes=15,
                priority="medium", frequency="weekly",
                last_completed_date="")
    assert task.is_due_today() is True


def test_weekly_task_excluded_from_plan_when_not_due():
    """A weekly task done 2 days ago must appear in not_due, not scheduled."""
    owner = make_owner()
    pet = make_pet()
    pet.add_task(Task(task_id="t1", title="Grooming", duration_minutes=15,
                      priority="medium", frequency="weekly",
                      last_completed_date=days_ago(2)))
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_plan()
    scheduled_titles = [t.title for _, t in plan["scheduled"]]
    not_due_titles   = [t.title for _, t in plan["not_due"]]
    assert "Grooming" not in scheduled_titles
    assert "Grooming" in not_due_titles


# ── Conflict detection ────────────────────────────────────────────────────────

def test_conflict_detected_for_same_start_time():
    """Two tasks starting at the same time must produce a conflict warning."""
    owner = make_owner()
    pet = make_pet()
    pet.add_task(Task(task_id="t1", title="Walk", duration_minutes=30,
                      priority="high", frequency="daily", start_time="08:00"))
    pet.add_task(Task(task_id="t2", title="Feed", duration_minutes=10,
                      priority="high", frequency="daily", start_time="08:00"))
    owner.add_pet(pet)

    conflicts = Scheduler(owner).detect_conflicts()
    assert len(conflicts) == 1
    assert "Walk" in conflicts[0]
    assert "Feed" in conflicts[0]


def test_conflict_detected_for_overlapping_windows():
    """Task B starting inside Task A's window must be flagged."""
    owner = make_owner()
    pet = make_pet()
    pet.add_task(Task(task_id="t1", title="Morning walk",
                      duration_minutes=30, priority="high", frequency="daily",
                      start_time="07:30"))   # window: 07:30–08:00
    pet.add_task(Task(task_id="t2", title="Feed breakfast",
                      duration_minutes=10, priority="high", frequency="daily",
                      start_time="07:45"))   # window: 07:45–07:55 → overlap
    owner.add_pet(pet)

    conflicts = Scheduler(owner).detect_conflicts()
    assert len(conflicts) == 1


def test_no_conflict_for_back_to_back_tasks():
    """Tasks that are adjacent but not overlapping must not be flagged."""
    owner = make_owner()
    pet = make_pet()
    pet.add_task(Task(task_id="t1", title="Walk", duration_minutes=30,
                      priority="high", frequency="daily", start_time="07:30"))
    # starts exactly when walk ends (08:00) → no overlap
    pet.add_task(Task(task_id="t2", title="Feed", duration_minutes=10,
                      priority="high", frequency="daily", start_time="08:00"))
    owner.add_pet(pet)

    conflicts = Scheduler(owner).detect_conflicts()
    assert len(conflicts) == 0


def test_no_conflict_without_start_times():
    """Tasks with no start_time must never trigger conflict warnings."""
    owner = make_owner()
    pet = make_pet()
    pet.add_task(Task(task_id="t1", title="Walk", duration_minutes=30,
                      priority="high", frequency="daily"))
    pet.add_task(Task(task_id="t2", title="Feed", duration_minutes=10,
                      priority="high", frequency="daily"))
    owner.add_pet(pet)

    conflicts = Scheduler(owner).detect_conflicts()
    assert len(conflicts) == 0


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_pet_with_no_tasks_does_not_crash():
    owner = make_owner()
    owner.add_pet(make_pet())
    plan = Scheduler(owner).generate_plan()
    assert plan["scheduled"] == []
    assert plan["skipped"] == []


def test_owner_with_no_pets_does_not_crash():
    plan = Scheduler(make_owner()).generate_plan()
    assert plan["scheduled"] == []


def test_all_tasks_exceed_budget_all_skipped():
    """When every task is longer than available time, all must be skipped."""
    owner = make_owner(minutes=10)
    pet = make_pet()
    pet.add_task(Task(task_id="t1", title="Long walk", duration_minutes=60,
                      priority="high", frequency="daily"))
    pet.add_task(Task(task_id="t2", title="Grooming", duration_minutes=45,
                      priority="medium", frequency="daily"))
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_plan()
    assert len(plan["scheduled"]) == 0
    assert len(plan["skipped"]) == 2
    assert plan["total_duration"] == 0


def test_completed_task_excluded_from_plan():
    """A task marked complete before planning must not appear in scheduled."""
    owner = make_owner()
    pet = make_pet()
    task = Task(task_id="t1", title="Walk", duration_minutes=20,
                priority="high", frequency="daily")
    task.complete()
    pet.add_task(task)
    owner.add_pet(pet)

    plan = Scheduler(owner).generate_plan()
    scheduled_titles = [t.title for _, t in plan["scheduled"]]
    assert "Walk" not in scheduled_titles


def test_filter_tasks_by_pet_name():
    owner = make_owner()
    mochi = make_pet("Mochi")
    luna  = make_pet("Luna")
    mochi.add_task(Task(task_id="t1", title="Walk", duration_minutes=20,
                        priority="high", frequency="daily"))
    luna.add_task(Task(task_id="t2", title="Litter", duration_minutes=10,
                       priority="high", frequency="daily"))
    owner.add_pet(mochi)
    owner.add_pet(luna)

    results = Scheduler(owner).filter_tasks(pet_name="Mochi")
    assert all(pet.name == "Mochi" for pet, _ in results)
    assert len(results) == 1


def test_filter_tasks_no_match_returns_empty():
    owner = make_owner()
    owner.add_pet(make_pet("Mochi"))
    results = Scheduler(owner).filter_tasks(pet_name="Ghost")
    assert results == []
