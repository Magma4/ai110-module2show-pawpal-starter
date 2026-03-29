"""Optional extension behaviors: JSON persistence and next-available slot."""

from datetime import date, datetime

from pawpal_system import Owner, Pet, Scheduler, Task


def test_owner_json_roundtrip(tmp_path):
    owner = Owner("Alex", available_minutes=90)
    pet = Pet("Luna", species="cat")
    owner.register_pet(pet)
    pet.add_task(
        Task(
            "Walk",
            duration_minutes=30,
            priority=3,
            due=datetime(2026, 6, 1, 8, 0),
            recurrence="daily",
        )
    )
    path = tmp_path / "data.json"
    owner.save_to_json(path)
    loaded = Owner.load_from_json(path)
    assert loaded.name == "Alex"
    assert loaded.available_minutes == 90
    assert len(loaded.pets) == 1
    assert loaded.pets[0].tasks[0].title == "Walk"
    assert loaded.pets[0].tasks[0].recurrence == "daily"


def test_next_available_slot_empty_calendar():
    owner = Owner("Sam", available_minutes=120)
    sched = Scheduler()
    day = date(2026, 6, 15)
    slot = sched.next_available_slot(owner, day, 30)
    assert slot is not None
    assert slot.date() == day
    assert slot.hour == 6


def test_next_available_slot_after_busy_block():
    owner = Owner("Sam")
    p = Pet("Rex")
    owner.register_pet(p)
    day = date(2026, 6, 1)
    p.add_task(Task("Block", due=datetime(2026, 6, 1, 6, 0), duration_minutes=30))
    sched = Scheduler()
    slot = sched.next_available_slot(owner, day, 30)
    assert slot == datetime(2026, 6, 1, 6, 30)


def test_sort_by_priority_then_time():
    a = Task("a", priority=1, due=datetime(2026, 1, 1, 12, 0))
    b = Task("b", priority=3, due=datetime(2026, 1, 1, 9, 0))
    c = Task("c", priority=3, due=datetime(2026, 1, 1, 8, 0))
    out = Scheduler().sort_by_priority_then_time([a, b, c])
    assert [t.title for t in out] == ["c", "b", "a"]
