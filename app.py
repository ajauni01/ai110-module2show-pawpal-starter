import uuid
import streamlit as st
from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# Step 2: Persist Owner in session state so it survives reruns
if "owner" not in st.session_state:
    st.session_state.owner = None

# ── Owner & Pet Setup ────────────────────────────────────────────────────────
st.subheader("Owner & Pet Setup")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
with col2:
    available_minutes = st.number_input(
        "Available minutes today", min_value=10, max_value=480, value=60
    )

col3, col4, col5 = st.columns(3)
with col3:
    pet_name = st.text_input("Pet name", value="Mochi")
with col4:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col5:
    pet_age = st.number_input("Pet age", min_value=0, max_value=30, value=2)

if st.button("Set Owner & Pet"):
    # Step 3: Wire button to Owner/Pet class methods
    owner = Owner(name=owner_name, available_minutes=int(available_minutes))
    owner.add_pet(Pet(name=pet_name, species=species, age=int(pet_age)))
    st.session_state.owner = owner
    st.success(f"Owner **{owner_name}** set with pet **{pet_name}** ({species}).")

st.divider()

# ── Add Tasks ────────────────────────────────────────────────────────────────
st.subheader("Add a Task")

if st.session_state.owner is None:
    st.info("Set up your owner and pet first.")
else:
    owner: Owner = st.session_state.owner

    pet_names = [p.name for p in owner.pets]
    selected_pet_name = st.selectbox("Assign to pet", pet_names)

    col6, col7, col8 = st.columns(3)
    with col6:
        task_title = st.text_input("Task title", value="Morning walk")
    with col7:
        duration = st.number_input(
            "Duration (minutes)", min_value=1, max_value=240, value=20
        )
    with col8:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    frequency = st.selectbox("Frequency", ["daily", "weekly", "as_needed"])

    if st.button("Add Task"):
        task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            frequency=frequency,
            task_id=str(uuid.uuid4())[:8],
        )
        # Step 3: Call pet.add_task() from pawpal_system
        for pet in owner.pets:
            if pet.name == selected_pet_name:
                pet.add_task(task)
                break
        st.success(f"Task **{task_title}** added to {selected_pet_name}.")

    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.write("Current tasks:")
        for pet, task in all_tasks:
            status = "✅ done" if task.is_completed else "⏳ pending"
            st.markdown(
                f"- **{task.title}** ({pet.name}) — "
                f"{task.duration_minutes} min · {task.priority} · {task.frequency} · {status}"
            )
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# ── Generate Schedule ────────────────────────────────────────────────────────
st.subheader("Generate Schedule")

if st.session_state.owner is None:
    st.info("Set up your owner and pet first.")
elif not st.session_state.owner.get_all_tasks():
    st.info("Add some tasks before generating a schedule.")
else:
    if st.button("Generate Schedule"):
        scheduler = Scheduler(st.session_state.owner)
        plan = scheduler.generate_plan()

        st.markdown(
            f"**Daily plan for {st.session_state.owner.name}** "
            f"({st.session_state.owner.available_minutes} min available)"
        )

        if plan["scheduled"]:
            st.markdown("**Scheduled:**")
            for pet, task in plan["scheduled"]:
                st.success(
                    f"✓ **{task.title}** for {pet.name} — "
                    f"{task.duration_minutes} min · {task.priority} priority"
                )

        if plan["skipped"]:
            st.markdown("**Skipped (not enough time):**")
            for pet, task in plan["skipped"]:
                st.warning(
                    f"✗ **{task.title}** for {pet.name} — "
                    f"needs {task.duration_minutes} min"
                )

        st.info(
            f"Time used: {plan['total_duration']} / "
            f"{st.session_state.owner.available_minutes} min  |  "
            f"Scheduled: {len(plan['scheduled'])}  |  "
            f"Skipped: {len(plan['skipped'])}"
        )
