from pawpal_system import Owner, Pet, Task, Scheduler


# --- Setup ---
owner = Owner(name="Jordan", available_minutes=90)

mochi = Pet(name="Mochi", species="dog", age=3)
luna = Pet(name="Luna", species="cat", age=5)

# Tasks for Mochi
mochi.add_task(Task(
    task_id="t1",
    title="Morning walk",
    duration_minutes=30,
    priority="high",
    frequency="daily",
))
mochi.add_task(Task(
    task_id="t2",
    title="Feed breakfast",
    duration_minutes=10,
    priority="high",
    frequency="daily",
))
mochi.add_task(Task(
    task_id="t3",
    title="Grooming brush",
    duration_minutes=15,
    priority="medium",
    frequency="weekly",
))

# Tasks for Luna
luna.add_task(Task(
    task_id="t4",
    title="Clean litter box",
    duration_minutes=10,
    priority="high",
    frequency="daily",
))
luna.add_task(Task(
    task_id="t5",
    title="Playtime",
    duration_minutes=20,
    priority="low",
    frequency="daily",
))

owner.add_pet(mochi)
owner.add_pet(luna)

# --- Schedule ---
scheduler = Scheduler(owner)

print("=" * 45)
print("         TODAY'S SCHEDULE")
print("=" * 45)
print(scheduler.explain_plan())
print("=" * 45)
