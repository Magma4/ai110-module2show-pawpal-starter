"""CLI demo: verify PawPal+ scheduling, sorting, filtering, and time conflicts."""

from __future__ import annotations

from datetime import date, datetime, time

from pawpal_system import Owner, Pet, Scheduler, Task


def print_schedule_table(
    planned: list[Task],
    *,
    title: str,
    subtitle: str,
) -> int:
    """Print an aligned table; return total minutes planned."""
    headers = ("#", "Task", "When", "Category", "Dur", "Pet", "Pri")
    rows: list[list[str]] = []
    total_min = 0
    for i, task in enumerate(planned, start=1):
        total_min += task.duration_minutes
        pet = task.pet.name if task.pet else "—"
        time_cell = (
            task.due.strftime("%H:%M") if task.due else (task.time_str or "—")
        )
        rows.append(
            [
                str(i),
                task.title,
                time_cell,
                task.category or "—",
                f"{task.duration_minutes} min",
                pet,
                str(task.priority),
            ]
        )

    table = [headers, *rows]
    widths = [
        max(len(table[r][c]) for r in range(len(table)))
        for c in range(len(headers))
    ]

    def line(cells: list[str], sep: str = " │ ") -> str:
        parts = [cells[i].ljust(widths[i]) for i in range(len(cells))]
        return sep.join(parts)

    rule = "─" * (sum(widths) + 3 * (len(headers) - 1))

    print()
    print(f"  {title}")
    print(f"  {subtitle}")
    print(f"  ┌{rule}┐")
    print(f"  │ {line(headers)} │")
    print(f"  ├{rule}┤")
    if not rows:
        print(f"  │ {'(no tasks scheduled)'.ljust(sum(widths) + 3 * (len(headers) - 1))} │")
    else:
        for row in rows:
            print(f"  │ {line(row)} │")
    print(f"  └{rule}┘")
    if planned:
        print(f"  Total: {total_min} min  ·  {len(planned)} task(s)")
    print()
    return total_min


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

    # Intentionally out of chronological order (by due / time_str)
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

    # Same start time, different pets — overlapping intervals (Step 4)
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

    print("\n  --- Sort by time (due / HH:MM) ---")
    by_time = scheduler.sort_by_time(pending_only)
    for t in by_time:
        tlabel = t.due.strftime("%H:%M") if t.due else t.time_str or "—"
        pet = t.pet.name if t.pet else "—"
        print(f"    {tlabel}  {t.title}  ({pet})")

    print("\n  --- Time overlap warnings ---")
    overlap_msgs = scheduler.detect_time_overlaps(pending_only, plan_date=today)
    if overlap_msgs:
        for line in overlap_msgs:
            print(f"    Warning: {line}")
    else:
        print("    (none)")

    planned, messages = scheduler.build_daily_plan(owner, plan_date=today)

    print_schedule_table(
        planned,
        title=f"Today's Schedule — {today.isoformat()}",
        subtitle=f"{owner.name}  ·  {owner.available_minutes} min available today",
    )

    print("  Planner notes")
    print("  " + "·" * 48)
    for line in messages:
        print(f"    • {line}")
    print()


if __name__ == "__main__":
    main()
