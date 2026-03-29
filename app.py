import streamlit as st
from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.caption(
    "Plan care from your owner profile, pets, and tasks. Data stays in this browser tab until you refresh."
)

# --- Session "memory": one Owner for the whole session (survives reruns) ---
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", available_minutes=60)

owner: Owner = st.session_state.owner

st.divider()
st.subheader("Owner")

col_o1, col_o2 = st.columns(2)
with col_o1:
    name_in = st.text_input("Owner name", value=owner.name, key="owner_name_input")
with col_o2:
    minutes_in = st.number_input(
        "Minutes available today",
        min_value=0,
        max_value=24 * 60,
        value=int(owner.available_minutes),
        step=15,
        key="owner_minutes_input",
    )

# Sync widgets → Owner on every run (Streamlit reruns the script; session_state keeps the object)
owner.name = name_in.strip() or "Owner"
try:
    owner.register()
except ValueError as e:
    st.error(str(e))
owner.set_available_time(int(minutes_in))

st.divider()
st.subheader("Pets")

with st.form("add_pet_form", clear_on_submit=True):
    pn = st.text_input("Pet name", key="pet_name_new")
    sp = st.selectbox("Species", ["dog", "cat", "rabbit", "other"], key="pet_species_new")
    add_pet_submitted = st.form_submit_button("Add pet")

if add_pet_submitted:
    if not pn.strip():
        st.warning("Enter a pet name.")
    else:
        pet = Pet(pn.strip(), species=sp)
        owner.register_pet(pet)
        st.success(f"Added {pet.name}.")

st.markdown("**Your pets**")
if owner.list_pets():
    for p in owner.list_pets():
        st.write(f"- **{p.name}** ({p.species}) — {len(p.tasks)} task(s)")
else:
    st.info("No pets yet. Add one above.")

st.divider()
st.subheader("Tasks")

_priority_to_int = {"low": 1, "medium": 2, "high": 3}

pet_choices = owner.list_pets()
if not pet_choices:
    st.warning("Add at least one pet before you add tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        pet_labels = [f"{p.name} ({p.species})" for p in pet_choices]
        pet_idx = st.selectbox(
            "Pet",
            options=list(range(len(pet_choices))),
            format_func=lambda i: pet_labels[int(i)],
            key="task_pet_pick",
        )
        t_title = st.text_input("Task title", value="Morning walk", key="task_title_new")
        t_dur = st.number_input(
            "Duration (minutes)", min_value=1, max_value=240, value=20, key="task_dur_new"
        )
        t_pri = st.selectbox(
            "Priority", ["low", "medium", "high"], index=2, key="task_pri_new"
        )
        add_task_submitted = st.form_submit_button("Add task")

    if add_task_submitted:
        pet_pick = pet_choices[int(pet_idx)]
        task = Task(
            t_title.strip() or "Task",
            duration_minutes=int(t_dur),
            priority=_priority_to_int[t_pri],
        )
        pet_pick.add_task(task)
        st.success(f"Added “{task.title}” for {pet_pick.name}.")

st.markdown("**Current tasks**")
rows: list[dict[str, str | int]] = []
for pet in owner.pets:
    for t in pet.tasks:
        rows.append(
            {
                "Pet": pet.name,
                "Title": t.title,
                "Minutes": t.duration_minutes,
                "Priority": t.priority,
            }
        )
if rows:
    st.dataframe(rows, use_container_width=True, hide_index=True)
else:
    st.info("No tasks yet.")

st.divider()
st.subheader("Today’s schedule")

if st.button("Generate schedule", key="gen_schedule"):
    scheduler = Scheduler()
    planned, messages = scheduler.build_daily_plan(owner, plan_date=date.today())
    st.session_state.last_plan = planned
    st.session_state.last_plan_messages = messages

if "last_plan" in st.session_state:
    planned = st.session_state.last_plan
    msgs = st.session_state.get("last_plan_messages", [])
    if planned:
        st.success(f"Planned {len(planned)} task(s) within {owner.available_minutes} min.")
        for i, task in enumerate(planned, start=1):
            pet_name = task.pet.name if task.pet else "—"
            st.write(f"{i}. **{task.title}** — {task.duration_minutes} min — {pet_name}")
    else:
        st.info("No tasks fit or no pending tasks.")
    with st.expander("Planner notes"):
        for line in msgs:
            st.caption(line)
