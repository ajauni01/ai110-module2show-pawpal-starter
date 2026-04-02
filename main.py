from pawpal_system import Owner, Pet, Task, Scheduler


# --- Setup ---
owner = Owner(name="Jordan", available_minutes=120)

mochi = Pet(name="Mochi", species="dog", age=3)
luna = Pet(name="Luna", species="cat", age=5)

# CONFLICT 1 (same pet): Morning walk 07:30–08:00 overlaps Feed breakfast 07:45–07:55
mochi.add_task(Task(
    task_id="t1",
    title="Morning walk",
    duration_minutes=30,
    priority="high",
    frequency="daily",
    preferred_time="morning",
    start_time="07:30",
))
mochi.add_task(Task(
    task_id="t2",
    title="Feed breakfast",
    duration_minutes=10,
    priority="high",
    frequency="daily",
    preferred_time="morning",
    start_time="07:45",            # starts inside the walk window → conflict
))

# No conflict: grooming starts after the walk ends
mochi.add_task(Task(
    task_id="t3",
    title="Grooming brush",
    duration_minutes=15,
    priority="medium",
    frequency="weekly",
    preferred_time="afternoon",
    start_time="14:00",
    last_completed_date="2026-03-26",
))

# CONFLICT 2 (different pets): Clean litter 08:30–08:40 overlaps Playtime 08:35–08:55
luna.add_task(Task(
    task_id="t4",
    title="Clean litter box",
    duration_minutes=10,
    priority="high",
    frequency="daily",
    preferred_time="morning",
    start_time="08:30",
))
luna.add_task(Task(
    task_id="t5",
    title="Playtime",
    duration_minutes=20,
    priority="low",
    frequency="daily",
    preferred_time="morning",
    start_time="08:35",            # starts inside litter-box window → conflict
))

# No conflict: evening walk starts well after everything else
mochi.add_task(Task(
    task_id="t6",
    title="Evening walk",
    duration_minutes=25,
    priority="medium",
    frequency="daily",
    preferred_time="evening",
    start_time="18:00",
))

owner.add_pet(mochi)
owner.add_pet(luna)

scheduler = Scheduler(owner)

# --- Conflict detection ---
print("=" * 55)
print("  CONFLICT DETECTION")
print("=" * 55)
conflicts = scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        print(warning)
else:
    print("No conflicts detected.")

# --- Tasks sorted by start time ---
print("\n" + "=" * 55)
print("  TASKS SORTED BY START TIME")
print("=" * 55)
for pet, task in scheduler.sort_by_time():
    time_label = task.start_time if task.start_time else "(no time)"
    print(f"  {time_label}  [{pet.name}] {task.title} ({task.duration_minutes} min)")

# --- Filtering ---
print("\n" + "=" * 55)
print("  FILTER: Mochi's pending tasks")
print("=" * 55)
for pet, task in scheduler.filter_tasks(pet_name="Mochi", completed=False):
    print(f"  {task}")

# --- Full schedule ---
print("\n" + "=" * 55)
print("  TODAY'S SCHEDULE")
print("=" * 55)
print(scheduler.explain_plan())
print("=" * 55)
