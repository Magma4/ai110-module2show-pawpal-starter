"""CLI demo: verify PawPal+ scheduling logic without Streamlit."""

from __future__ import annotations

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    owner = Owner("Alex Rivera", available_minutes=120)
    owner.register()
    owner.set_available_time(120)

    luna = Pet("Luna", species="cat")
    max_ = Pet("Max", species="dog")
    owner.register_pet(luna)
    owner.register_pet(max_)

    luna.add_task(
        Task(
            "Morning feeding",
            category="feeding",
            duration_minutes=15,
            priority=3,
        )
    )
    luna.add_task(
        Task(
            "Play / enrichment",
            category="enrichment",
            duration_minutes=25,
            priority=2,
        )
    )
    max_.add_task(
        Task(
            "Neighborhood walk",
            category="walk",
            duration_minutes=45,
            priority=5,
        )
    )
    max_.add_task(
        Task(
            "Evening meds",
            category="medication",
            duration_minutes=10,
            priority=4,
        )
    )

    scheduler = Scheduler()
    today = date.today()
    planned, messages = scheduler.build_daily_plan(owner, plan_date=today)

    print()
    print("=" * 56)
    print(f"  Today's Schedule — {today.isoformat()}")
    print(f"  Owner: {owner.name}  |  Time available: {owner.available_minutes} min")
    print("=" * 56)

    if not planned:
        print("  (No tasks fit in the available time today.)")
    else:
        total = 0
        for i, task in enumerate(planned, start=1):
            pet_name = task.pet.name if task.pet else "—"
            total += task.duration_minutes
            print(
                f"  {i}. {task.title}  [{task.category or 'task'}]  "
                f"| {task.duration_minutes} min  | priority {task.priority}  | {pet_name}"
            )
        print("-" * 56)
        print(f"  Planned: {total} min  |  {len(planned)} task(s)")

    print()
    print("Notes:")
    for line in messages:
        print(f"  • {line}")
    print()


if __name__ == "__main__":
    main()
