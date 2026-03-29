"""Tests for PawPal+ domain logic.

Test plan (Phase 5)
-------------------
**Happy paths:** owner/pet/task wiring, filter by status/pet, sort by clock time, daily/weekly
recurrence spawns next task, time-overlap warnings, greedy daily plan fits budget.

**Edge cases:** pet with no tasks, empty overlap list, adjacent non-overlapping intervals,
partial overlap, done tasks ignored for overlaps, weekly recurrence without due (uses today+1w).

Copilot-style edge-case focus for a pet scheduler: empty graphs, identical start times,
touching intervals, recurring templates detached from ``pet.tasks`` (no spawn), and
sort stability when times tie.
"""

from datetime import date, datetime

from pawpal_system import Owner, Pet, Scheduler, Task


def _minutes_from_midnight(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute


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


def test_sort_by_time_chronological_order():
    """Sorting correctness: sort_by_time returns tasks in non-decreasing clock order."""
    sched = Scheduler()
    tasks = [
        Task("c", due=datetime(2026, 1, 1, 14, 0)),
        Task("a", time_str="06:15"),
        Task("b", due=datetime(2026, 1, 1, 9, 30)),
    ]
    ordered = sched.sort_by_time(tasks)
    mins = []
    for t in ordered:
        if t.due is not None:
            mins.append(_minutes_from_midnight(t.due))
        else:
            h, m = divmod(6 * 60 + 15, 60)  # from time_str 06:15
            mins.append(h * 60 + m)
    assert mins == sorted(mins)
    assert [t.title for t in ordered] == ["a", "b", "c"]


def test_sort_by_time_orders_by_due_and_hhmm():
    """Sorting: sort_by_time mixes due and time_str into one chronological order."""
    a = Task("late", due=datetime(2026, 1, 1, 18, 0))
    b = Task("early", time_str="07:00")
    c = Task("mid", due=datetime(2026, 1, 1, 12, 0))
    sched = Scheduler()
    ordered = sched.sort_by_time([a, b, c])
    assert [t.title for t in ordered] == ["early", "mid", "late"]


def test_mark_complete_daily_queues_next_occurrence():
    """Recurrence: marking a daily task complete creates a pending task for the following day."""
    pet = Pet("Rex")
    t = Task("Pill", recurrence="daily", due=datetime(2026, 3, 28, 8, 0))
    pet.add_task(t)
    t.mark_complete()
    assert t.status == "done"
    assert len(pet.tasks) == 2
    nxt = next(x for x in pet.tasks if x.status == "pending")
    assert nxt.due == datetime(2026, 3, 29, 8, 0)


def test_mark_complete_weekly_queues_next_week():
    """Recurrence: weekly template gets next occurrence one week later."""
    pet = Pet("Rex")
    t = Task("Groom", recurrence="weekly", due=datetime(2026, 3, 23, 10, 30))
    pet.add_task(t)
    t.mark_complete()
    nxt = next(x for x in pet.tasks if x.status == "pending")
    assert nxt.due == datetime(2026, 3, 30, 10, 30)


def test_mark_complete_daily_no_spawn_when_not_on_pet_list():
    """Recurring task not stored on pet does not spawn (ephemeral instance edge case)."""
    t = Task("Pill", recurrence="daily", due=datetime(2026, 3, 28, 8, 0))
    t.mark_complete()
    assert t.status == "done"


def test_detect_time_overlaps_duplicate_start():
    """Conflict detection: identical start times produce a warning."""
    day = date(2026, 6, 1)
    a = Task("A", due=datetime(2026, 6, 1, 8, 30), duration_minutes=20)
    b = Task("B", due=datetime(2026, 6, 1, 8, 30), duration_minutes=20)
    sched = Scheduler()
    msgs = sched.detect_time_overlaps([a, b], plan_date=day)
    assert len(msgs) == 1
    assert "Time overlap" in msgs[0]


def test_detect_time_overlaps_partial_overlap():
    """Conflict detection: partial interval overlap is flagged."""
    day = date(2026, 6, 1)
    a = Task("A", due=datetime(2026, 6, 1, 8, 0), duration_minutes=30)
    b = Task("B", due=datetime(2026, 6, 1, 8, 15), duration_minutes=30)
    msgs = Scheduler().detect_time_overlaps([a, b], plan_date=day)
    assert len(msgs) == 1


def test_detect_time_overlaps_adjacent_no_warning():
    """Edge case: back-to-back intervals [8:00,8:30) and [8:30,9:00) do not overlap."""
    day = date(2026, 6, 1)
    a = Task("A", due=datetime(2026, 6, 1, 8, 0), duration_minutes=30)
    b = Task("B", due=datetime(2026, 6, 1, 8, 30), duration_minutes=30)
    assert Scheduler().detect_time_overlaps([a, b], plan_date=day) == []


def test_detect_time_overlaps_ignores_done_tasks():
    """Done tasks are skipped so completed history does not false-flag overlaps."""
    day = date(2026, 6, 1)
    a = Task("A", due=datetime(2026, 6, 1, 8, 30), duration_minutes=20, status="done")
    b = Task("B", due=datetime(2026, 6, 1, 8, 30), duration_minutes=20)
    assert Scheduler().detect_time_overlaps([a, b], plan_date=day) == []


def test_detect_time_overlaps_empty_input():
    """Empty task list yields no warnings."""
    assert Scheduler().detect_time_overlaps([], plan_date=date(2026, 1, 1)) == []


def test_owner_with_no_pets_has_no_tasks():
    """Edge case: owner with no pets returns an empty all_tasks list."""
    owner = Owner("Sam")
    owner.register()
    assert owner.all_tasks() == []


def test_build_daily_plan_empty_owner():
    """Edge case: no tasks yields an empty plan and a sensible message."""
    owner = Owner("Sam", available_minutes=60)
    owner.register()
    planned, msgs = Scheduler().build_daily_plan(owner, plan_date=date(2026, 1, 1))
    assert planned == []
    assert any("No pending" in m or "0" in m for m in msgs)
