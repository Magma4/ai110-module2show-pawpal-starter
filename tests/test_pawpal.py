"""Tests for PawPal+ domain logic."""

from datetime import date, datetime

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_sets_status_to_done():
    """Task completion: mark_complete() updates status."""
    task = Task("Morning walk", status="pending")
    task.mark_complete()
    assert task.status == "done"


def test_add_task_increases_pet_task_count():
    """Task addition: add_task appends to the pet's task list."""
    pet = Pet("Luna")
    assert len(pet.tasks) == 0
    task = Task("Feed")
    pet.add_task(task)
    assert len(pet.tasks) == 1
    assert pet.tasks[0] is task
    assert task.pet is pet


def test_filter_tasks_by_status_and_pet():
    """Filtering: status and pet_name narrow the task list."""
    pet_a = Pet("Luna")
    pet_b = Pet("Max")
    t1 = Task("A", status="pending")
    t2 = Task("B", status="done")
    pet_a.add_task(t1)
    pet_b.add_task(t2)
    sched = Scheduler()
    all_tasks = [t1, t2]
    assert len(sched.filter_tasks(all_tasks, status="pending")) == 1
    assert len(sched.filter_tasks(all_tasks, pet_name="Luna")) == 1


def test_sort_by_time_orders_by_due_and_hhmm():
    """Sorting: sort_by_time uses due, then time_str (HH:MM)."""
    a = Task("late", due=datetime(2026, 1, 1, 18, 0))
    b = Task("early", time_str="07:00")
    c = Task("mid", due=datetime(2026, 1, 1, 12, 0))
    sched = Scheduler()
    ordered = sched.sort_by_time([a, b, c])
    assert [t.title for t in ordered] == ["early", "mid", "late"]


def test_mark_complete_daily_queues_next_occurrence():
    """Recurring: daily template gets a pending follow-up with due +1 day."""
    pet = Pet("Rex")
    t = Task("Pill", recurrence="daily", due=datetime(2026, 3, 28, 8, 0))
    pet.add_task(t)
    t.mark_complete()
    assert t.status == "done"
    assert len(pet.tasks) == 2
    nxt = next(x for x in pet.tasks if x.status == "pending")
    assert nxt.due == datetime(2026, 3, 29, 8, 0)


def test_detect_time_overlaps_returns_warning_strings():
    """Time conflicts: overlapping intervals yield warnings (no exceptions)."""
    day = date(2026, 6, 1)
    a = Task("A", due=datetime(2026, 6, 1, 8, 30), duration_minutes=20)
    b = Task("B", due=datetime(2026, 6, 1, 8, 30), duration_minutes=20)
    sched = Scheduler()
    msgs = sched.detect_time_overlaps([a, b], plan_date=day)
    assert len(msgs) == 1
    assert "Time overlap" in msgs[0]
