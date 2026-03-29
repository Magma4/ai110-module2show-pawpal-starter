from pathlib import Path

import streamlit as st
from datetime import date, datetime

from pawpal_system import Owner, Pet, Scheduler, Task

DATA_PATH = Path("data.json")

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.caption(
    "Plan care from your owner profile, pets, and tasks. "
    "Your data is saved to **data.json** in the app working directory when possible."
)

# --- Session memory + optional JSON persistence ---
if "owner" not in st.session_state:
    if DATA_PATH.exists():
        try:
            st.session_state.owner = Owner.load_from_json(DATA_PATH)
        except (OSError, ValueError, KeyError):
            st.session_state.owner = Owner("Jordan", available_minutes=60)
    else:
        st.session_state.owner = Owner("Jordan", available_minutes=60)

owner: Owner = st.session_state.owner
today = date.today()
scheduler = Scheduler()

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
        t_time = st.text_input(
            "Time today (optional, HH:MM)",
            placeholder="08:30",
            help="Used for sorting and overlap checks on today's date.",
            key="task_time_str",
        )
        t_rec = st.selectbox(
            "Repeat",
            ["—", "daily", "weekly"],
            help="Daily/weekly tasks spawn the next occurrence when marked complete.",
            key="task_recurrence",
        )
        add_task_submitted = st.form_submit_button("Add task")

    if add_task_submitted:
        pet_pick = pet_choices[int(pet_idx)]
        rec = "" if t_rec == "—" else t_rec
        due: datetime | None = None
        ts = (t_time or "").strip()
        parse_error = False
        if ts:
            if ":" not in ts:
                parse_error = True
                st.warning("Time must look like HH:MM (e.g. 08:30).")
            else:
                try:
                    h, m = ts.split(":", 1)
                    due = datetime.combine(
                        today, datetime.min.time().replace(hour=int(h), minute=int(m))
                    )
                except ValueError:
                    parse_error = True
                    st.warning("Could not parse time — use HH:MM (e.g. 08:30).")
        if not parse_error:
            task = Task(
                t_title.strip() or "Task",
                duration_minutes=int(t_dur),
                priority=_priority_to_int[t_pri],
                due=due,
                time_str="" if due else ts,
                recurrence=rec,
            )
            pet_pick.add_task(task)
            st.success(f"Added “{task.title}” for {pet_pick.name}.")

st.markdown("**Current tasks**")
rows: list[dict[str, str | int]] = []
for pet in owner.pets:
    for t in pet.tasks:
        when = t.due.strftime("%Y-%m-%d %H:%M") if t.due else (t.time_str or "—")
        rows.append(
            {
                "Pri": f"{t.priority_emoji()} {t.priority_label()}",
                "Pet": pet.name,
                "Title": t.title,
                "When": when,
                "Minutes": t.duration_minutes,
                "Repeat": t.recurrence or "—",
                "Status": t.status,
            }
        )
if rows:
    st.dataframe(rows, use_container_width=True, hide_index=True)
else:
    st.info("No tasks yet.")

# --- Algorithmic layer: filter, sort, conflicts (always reflect latest data) ---
st.divider()
st.subheader("Smart scheduling")

pending = scheduler.filter_tasks(owner.all_tasks(), status="pending")
by_pri_time = scheduler.sort_by_priority_then_time(pending)

if by_pri_time:
    st.markdown("**Pending tasks — priority first, then time**")
    view = []
    for t in by_pri_time:
        pet_name = t.pet.name if t.pet else "—"
        if t.due and t.due.date() == today:
            when = t.due.strftime("%H:%M")
        elif t.due:
            when = t.due.strftime("%Y-%m-%d %H:%M")
        else:
            when = t.time_str or "—"
        view.append(
            {
                "Pri": f"{t.priority_emoji()} {t.priority_label()}",
                "When": when,
                "Task": t.title,
                "Pet": pet_name,
                "Min": t.duration_minutes,
            }
        )
    st.table(view)
else:
    st.caption("No pending tasks to sort.")

slot30 = scheduler.next_available_slot(owner, today, 30)
if slot30:
    st.info(
        f"**Next 30‑min opening:** {slot30.strftime('%H:%M')} today "
        "(based on timed tasks between 06:00–22:00)."
    )
else:
    st.caption("No contiguous 30‑minute slot found in the default day window.")

overlap_msgs = scheduler.detect_time_overlaps(pending, plan_date=today)
if overlap_msgs:
    st.warning(
        "**Overlapping times** — two or more tasks need you at the same clock time. "
        "Consider moving one task, shortening duration, or splitting care between people."
    )
    for msg in overlap_msgs:
        st.warning("⚠️ " + msg)
else:
    st.success("No time overlaps detected for tasks that have a time set for today.")

budget_msgs = scheduler.detect_conflicts(owner)
if budget_msgs:
    for msg in budget_msgs:
        st.warning("⏱️ " + msg)
else:
    st.caption("Total pending work fits your available minutes (or no timed workload conflict).")

st.divider()
st.subheader("Today’s plan")

if st.button("Generate schedule", key="gen_schedule"):
    planned, messages = scheduler.build_daily_plan(owner, plan_date=today)
    st.session_state.last_plan = planned
    st.session_state.last_plan_messages = messages

if "last_plan" in st.session_state:
    planned = st.session_state.last_plan
    msgs = st.session_state.get("last_plan_messages", [])
    if planned:
        st.success(
            f"**{len(planned)} task(s)** lined up for today within **{owner.available_minutes} min** available."
        )
        plan_rows = []
        for i, task in enumerate(planned, start=1):
            pet_name = task.pet.name if task.pet else "—"
            plan_rows.append(
                {
                    "#": i,
                    "Pri": f"{task.priority_emoji()} {task.priority_label()}",
                    "Task": task.title,
                    "Minutes": task.duration_minutes,
                    "Pet": pet_name,
                }
            )
        st.table(plan_rows)
        st.caption("Order follows **priority** (greedy fit to your time budget), not clock time.")
        with st.expander("Same plan sorted by clock time"):
            st.table(
                [
                    {
                        "When": (
                            task.due.strftime("%H:%M")
                            if task.due and task.due.date() == today
                            else (task.time_str or "—")
                        ),
                        "Task": task.title,
                        "Pet": task.pet.name if task.pet else "—",
                    }
                    for task in scheduler.sort_by_time(list(planned))
                ]
            )
    else:
        st.info("No tasks fit or no pending tasks for today.")
    with st.expander("Planner notes"):
        for line in msgs:
            st.caption(line)

# Persist owner graph for next session (best-effort)
try:
    owner.save_to_json(DATA_PATH)
except OSError:
    pass
