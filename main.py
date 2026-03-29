"""CLI demo: verify PawPal+ scheduling, sorting, filtering, conflicts, and formatting."""

from __future__ import annotations

from datetime import date, datetime, time

from tabulate import tabulate

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    today = date.today()
    owner = Owner("Alex Rivera", available_minutes=120)
    owner.register()
    owner.set_available_time(120)

    luna = Pet("Luna", species="cat")
    max_ = Pet("Max", species="dog")
    owner.register_pet(luna)
    owner.register_pet(max_)

    def at(hour: int, minute: int = 0) -> datetime:
        return datetime.combine(today, time(hour, minute))

    luna.add_task(
        Task(
            "Afternoon nap check",
            category="care",
            duration_minutes=5,
            priority=1,
            due=at(14, 30),
        )
    )
    max_.add_task(
        Task(
            "Neighborhood walk",
            category="walk",
            duration_minutes=45,
            priority=5,
            due=at(7, 0),
        )
    )
    luna.add_task(
        Task(
            "Morning feeding",
            category="feeding",
            duration_minutes=15,
            priority=3,
            time_str="08:00",
        )
    )
    max_.add_task(
        Task(
            "Evening meds",
            category="medication",
            duration_minutes=10,
            priority=4,
            time_str="21:00",
        )
    )
    luna.add_task(
        Task(
            "Brush fur",
            category="grooming",
            duration_minutes=20,
            priority=2,
            due=at(8, 30),
        )
    )
    max_.add_task(
        Task(
            "Dental chew",
            category="dental",
            duration_minutes=20,
            priority=2,
            due=at(8, 30),
        )
    )

    scheduler = Scheduler()
    all_tasks = owner.all_tasks()

    print("  --- Filter: pending only ---")
    pending_only = scheduler.filter_tasks(all_tasks, status="pending")
    print(f"  Count: {len(pending_only)}")

    print("\n  --- Priority → time (smart view) ---")
    pri_time = scheduler.sort_by_priority_then_time(pending_only)
    pt_rows = [
        [
            t.priority_emoji(),
            t.priority_label(),
            t.due.strftime("%H:%M") if t.due else (t.time_str or "—"),
            t.title,
            t.pet.name if t.pet else "—",
        ]
        for t in pri_time
    ]
    print(tabulate(pt_rows, headers=["", "Priority", "When", "Task", "Pet"], tablefmt="simple"))

    print("\n  --- Sort by time only ---")
    by_time = scheduler.sort_by_time(pending_only)
    for t in by_time:
        tlabel = t.due.strftime("%H:%M") if t.due else t.time_str or "—"
        pet = t.pet.name if t.pet else "—"
        print(f"    {tlabel}  {t.title}  ({pet})")

    slot = scheduler.next_available_slot(owner, today, 30)
    print("\n  --- Next 30-minute opening ---")
    print(f"    {slot.strftime('%H:%M')}" if slot else "    (none in 06:00–22:00 window)")

    print("\n  --- Time overlap warnings ---")
    overlap_msgs = scheduler.detect_time_overlaps(pending_only, plan_date=today)
    if overlap_msgs:
        for line in overlap_msgs:
            print(f"    Warning: {line}")
    else:
        print("    (none)")

    planned, messages = scheduler.build_daily_plan(owner, plan_date=today)

    print(f"\n  Today's Schedule — {today.isoformat()}  |  {owner.name}  |  {owner.available_minutes} min available")
    plan_rows = []
    for i, task in enumerate(planned, start=1):
        when = task.due.strftime("%H:%M") if task.due else (task.time_str or "—")
        plan_rows.append(
            [
                i,
                f"{task.priority_emoji()} {task.priority_label()}",
                task.title,
                when,
                task.category or "—",
                f"{task.duration_minutes} min",
                task.pet.name if task.pet else "—",
            ]
        )
    print(
        tabulate(
            plan_rows,
            headers=["#", "Priority", "Task", "When", "Category", "Dur", "Pet"],
            tablefmt="rounded_outline",
        )
    )

    print("\n  Planner notes")
    print("  " + "·" * 48)
    for line in messages:
        print(f"    • {line}")
    print()


if __name__ == "__main__":
    main()
