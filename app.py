import uuid
import streamlit as st
from pawpal_system import Owner, Pet, Scheduler, Task


def _md_table(rows: list[dict]) -> None:
    """Render a list of dicts as a markdown table — no pandas required."""
    if not rows:
        return
    headers = list(rows[0].keys())
    header_row = "| " + " | ".join(headers) + " |"
    sep_row = "| " + " | ".join("---" for _ in headers) + " |"
    data_rows = [
        "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |"
        for row in rows
    ]
    st.markdown("\n".join([header_row, sep_row] + data_rows))

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Smart pet care scheduling — priority-aware, conflict-free, and time-budgeted.")

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

    col9, col10, col11 = st.columns(3)
    with col9:
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as_needed"])
    with col10:
        preferred_time = st.selectbox(
            "Preferred time", ["any", "morning", "afternoon", "evening"]
        )
    with col11:
        start_time = st.text_input(
            "Start time (HH:MM)", value="", placeholder="e.g. 08:30"
        )

    if st.button("Add Task"):
        # Validate start_time format if provided
        valid_time = True
        if start_time:
            parts = start_time.split(":")
            valid_time = (
                len(parts) == 2
                and parts[0].isdigit()
                and parts[1].isdigit()
                and 0 <= int(parts[0]) <= 23
                and 0 <= int(parts[1]) <= 59
            )
            if not valid_time:
                st.error("Start time must be in HH:MM format (e.g. 08:30).")

        if valid_time:
            task = Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority,
                frequency=frequency,
                task_id=str(uuid.uuid4())[:8],
                preferred_time=preferred_time,
                start_time=start_time,
            )
            for pet in owner.pets:
                if pet.name == selected_pet_name:
                    pet.add_task(task)
                    break
            st.success(f"Task **{task_title}** added to {selected_pet_name}.")

    all_tasks = owner.get_all_tasks()
    if all_tasks:
        st.write("**Current tasks:**")
        rows = []
        for pet, task in all_tasks:
            rows.append({
                "Pet": pet.name,
                "Task": task.title,
                "Duration (min)": task.duration_minutes,
                "Priority": task.priority,
                "Frequency": task.frequency,
                "Start Time": task.start_time or "—",
                "Preferred Slot": task.preferred_time,
                "Status": "✅ done" if task.is_completed else "⏳ pending",
            })
        _md_table(rows)
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# ── Sorted Task View ─────────────────────────────────────────────────────────
st.subheader("Sorted Task View")

if st.session_state.owner is None or not st.session_state.owner.get_all_tasks():
    st.info("Add tasks to see them sorted by scheduled time.")
else:
    owner: Owner = st.session_state.owner
    scheduler = Scheduler(owner)

    # Filter controls
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filter_pet = st.selectbox(
            "Filter by pet",
            ["All pets"] + [p.name for p in owner.pets],
            key="filter_pet",
        )
    with col_f2:
        filter_status = st.selectbox(
            "Filter by status",
            ["All", "Pending only", "Completed only"],
            key="filter_status",
        )

    # Apply filter_tasks from Scheduler
    pet_name_arg = None if filter_pet == "All pets" else filter_pet
    completed_arg = (
        None
        if filter_status == "All"
        else (filter_status == "Completed only")
    )
    filtered = scheduler.filter_tasks(pet_name=pet_name_arg, completed=completed_arg)

    # Then sort the filtered results by start_time
    sorted_filtered = sorted(
        filtered,
        key=lambda x: (x[1].start_time == "", x[1].start_time),
    )

    if sorted_filtered:
        rows = []
        for pet, task in sorted_filtered:
            rows.append({
                "Pet": pet.name,
                "Task": task.title,
                "Start Time": task.start_time or "—",
                "Duration (min)": task.duration_minutes,
                "Priority": task.priority,
                "Status": "✅ done" if task.is_completed else "⏳ pending",
            })
        _md_table(rows)
    else:
        st.info("No tasks match the selected filters.")

    # ── Conflict Detection ───────────────────────────────────────────────────
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.markdown("**Scheduling Conflicts Detected:**")
        for warning in conflicts:
            st.warning(warning)
    else:
        timed_count = sum(
            1 for _, task in owner.get_all_tasks() if task.start_time
        )
        if timed_count >= 2:
            st.success("No scheduling conflicts — all timed tasks fit without overlap.")

st.divider()

# ── Generate Schedule ────────────────────────────────────────────────────────
st.subheader("Generate Daily Schedule")

if st.session_state.owner is None:
    st.info("Set up your owner and pet first.")
elif not st.session_state.owner.get_all_tasks():
    st.info("Add some tasks before generating a schedule.")
else:
    if st.button("Generate Schedule"):
        owner: Owner = st.session_state.owner
        scheduler = Scheduler(owner)
        plan = scheduler.generate_plan()

        st.markdown(
            f"**Daily plan for {owner.name}** "
            f"({owner.available_minutes} min available)"
        )

        # Show conflicts at the top so the owner sees them immediately
        if plan["conflicts"]:
            st.markdown("**⚠ Conflict Warnings — resolve these before your day starts:**")
            for warning in plan["conflicts"]:
                st.warning(warning)

        if plan["scheduled"]:
            st.markdown("**Scheduled tasks:**")
            for pet, task in plan["scheduled"]:
                time_label = f" · starts {task.start_time}" if task.start_time else ""
                st.success(
                    f"✓ **{task.title}** for {pet.name} — "
                    f"{task.duration_minutes} min · {task.priority} priority"
                    f" · {task.preferred_time}{time_label}"
                )

        if plan["skipped"]:
            st.markdown("**Skipped (not enough time today):**")
            for pet, task in plan["skipped"]:
                st.warning(
                    f"✗ **{task.title}** for {pet.name} — "
                    f"needs {task.duration_minutes} min · {task.priority} priority"
                )

        if plan["not_due"]:
            st.markdown("**Not due today (weekly cooldown active):**")
            for pet, task in plan["not_due"]:
                st.info(
                    f"— **{task.title}** for {pet.name} — "
                    f"weekly task, last done {task.last_completed_date}"
                )

        st.info(
            f"Time used: **{plan['total_duration']} / {owner.available_minutes} min**  |  "
            f"Scheduled: **{len(plan['scheduled'])}**  |  "
            f"Skipped: **{len(plan['skipped'])}**  |  "
            f"Not due: **{len(plan['not_due'])}**"
        )

        with st.expander("Show plan explanation"):
            for line in plan["explanation"]:
                st.text(line)
