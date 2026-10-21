import streamlit as st

from pawpal_system import Owner, Pet, Priority, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# --- App memory -------------------------------------------------------------
# Streamlit reruns this script on every click, so keep the Owner in session_state
# and only create it the first time.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", available_minutes=120)

owner: Owner = st.session_state.owner

CATEGORIES = ["exercise", "feeding", "medication", "grooming", "hygiene", "enrichment", "general"]

# --- Owner -------------------------------------------------------------------
st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)
owner.available_minutes = int(
    st.number_input(
        "Time available today (minutes)", min_value=0, max_value=1440, value=owner.available_minutes
    )
)
owner.preferences = st.multiselect(
    "Preferred task categories", CATEGORIES, default=owner.preferences
)

st.divider()

# --- Pets --------------------------------------------------------------------
st.subheader("Pets")
with st.form("add_pet", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        pet_name = st.text_input("Pet name")
    with col2:
        species = st.selectbox("Species", ["dog", "cat", "other"])
    with col3:
        age = st.number_input("Age", min_value=0, max_value=40, value=1)
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.error("Please enter a pet name.")
        elif any(p.name == pet_name.strip() for p in owner.pets):
            st.error(f"{pet_name.strip()} is already registered.")
        else:
            owner.add_pet(Pet(pet_name.strip(), species, int(age)))
            st.success(f"Added {pet_name.strip()}.")

if owner.pets:
    st.table(
        [{"name": p.name, "species": p.species, "age": p.age, "tasks": len(p.tasks)} for p in owner.pets]
    )
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Tasks -------------------------------------------------------------------
st.subheader("Tasks")
if not owner.pets:
    st.caption("Add a pet before adding tasks.")
else:
    with st.form("add_task", clear_on_submit=True):
        target = st.selectbox("For pet", [p.name for p in owner.pets])
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Task title", value="Morning walk")
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
            frequency = st.selectbox("Frequency", ["daily", "weekly", "once"])
        with col2:
            category = st.selectbox("Category", CATEGORIES)
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
            has_time = st.checkbox("Set a preferred time")
            preferred = st.time_input("Preferred time")
        if st.form_submit_button("Add task"):
            pet = next(p for p in owner.pets if p.name == target)
            try:
                pet.add_task(
                    Task(
                        title,
                        category,
                        int(duration),
                        Priority[priority.upper()],
                        preferred if has_time else None,
                        frequency,
                    )
                )
                st.success(f"Added '{title}' for {pet.name}.")
            except ValueError as err:
                st.error(str(err))

    all_tasks = Scheduler(owner).sort_by_time()
    if all_tasks:
        st.table(
            [
                {
                    "pet": t.pet_name,
                    "task": t.title,
                    "category": t.category,
                    "minutes": t.duration_minutes,
                    "priority": t.priority.name.lower(),
                    "due": str(t.due_date),
                    "time": t.preferred_time.strftime("%H:%M") if t.preferred_time else "anytime",
                    "frequency": t.frequency,
                    "done": t.completed,
                }
                for t in all_tasks
            ]
        )
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# --- Schedule ----------------------------------------------------------------
st.subheader("Build Schedule")
if st.button("Generate schedule"):
    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()
    for warning in scheduler.detect_conflicts(plan):
        st.warning(warning)
    if not plan:
        st.warning("Nothing could be scheduled. Add tasks or increase your available time.")
    for pet in owner.pets:
        pet_tasks = [t for t in plan if t.pet_name == pet.name]
        if not pet_tasks:
            continue
        st.markdown(f"**Daily plan for {pet.name} ({pet.species.title()})**")
        for t in pet_tasks:
            when = t.preferred_time.strftime("%H:%M") if t.preferred_time else "Anytime"
            st.markdown(
                f"- {when} — {t.title} ({t.duration_minutes} min) [priority: {t.priority.name.lower()}]"
            )
    with st.expander("Why this plan?"):
        st.text(scheduler.explain_plan())
