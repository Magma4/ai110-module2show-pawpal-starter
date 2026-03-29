"""PawPal+ logic layer: domain models and scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from itertools import combinations
from typing import Any


def _hhmm_sort_key(s: str) -> tuple[int, int]:
    """Parse ``s`` as ``HH:MM`` and return ``(hour, minute)`` for sorting; ``(99, 99)`` if invalid."""
    s = s.strip()
    if not s or ":" not in s:
        return (99, 99)
    part = s.split(":", 1)
    try:
        return (int(part[0]), int(part[1]))
    except ValueError:
        return (99, 99)


@dataclass
class Owner:
    name: str
    available_minutes: int = 0
    preferences: dict[str, Any] = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def register(self) -> None:
        """Reject empty owner names."""
        if not str(self.name).strip():
            raise ValueError("Owner name cannot be empty")

    def register_pet(self, pet: Pet) -> None:
        """Link a pet to this owner and keep both sides consistent."""
        pet.owner = self
        if pet not in self.pets:
            self.pets.append(pet)

    def set_available_time(self, minutes: int) -> None:
        """Store minutes available for scheduling today."""
        if minutes < 0:
            raise ValueError("available_minutes cannot be negative")
        self.available_minutes = minutes

    def list_pets(self) -> list[Pet]:
        """Return a copy of this owner's pet list."""
        return list(self.pets)

    def all_tasks(self) -> list[Task]:
        """List every task on every pet, in pet then task order."""
        out: list[Task] = []
        for pet in self.pets:
            out.extend(pet.tasks)
        return out


@dataclass
class Pet:
    name: str
    species: str = ""
    owner: Owner | None = None
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def update_profile(self, **kwargs: Any) -> None:
        """Apply name, species, or notes from keyword arguments."""
        allowed = {"name", "species", "notes"}
        for key, value in kwargs.items():
            if key in allowed:
                setattr(self, key, value)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet, moving it from another pet if needed."""
        if task.pet is not None and task.pet is not self:
            task.pet.remove_task(task)
        task.pet = self
        if task not in self.tasks:
            self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet and clear its pet link."""
        if task in self.tasks:
            self.tasks.remove(task)
        if task.pet is self:
            task.pet = None


@dataclass
class Task:
    title: str
    category: str = ""
    duration_minutes: int = 0
    priority: int = 0
    pet: Pet | None = None
    due: datetime | None = None
    time_str: str = ""
    recurrence: str = ""
    status: str = "pending"

    @property
    def frequency(self) -> str:
        """Return the recurrence string (same as ``recurrence``)."""
        return self.recurrence

    @frequency.setter
    def frequency(self, value: str) -> None:
        """Set recurrence using the frequency alias."""
        self.recurrence = value

    def mark_complete(self) -> None:
        """Set status to done; for daily/weekly templates on a pet, queue the next occurrence."""
        self.status = "done"
        pet = self.pet
        r = (self.recurrence or "").strip().lower()
        if pet is None or r not in ("daily", "weekly"):
            return
        if self not in pet.tasks:
            return
        next_due = self._next_occurrence_due()
        if next_due is None:
            return
        next_task = replace(self, status="pending", due=next_due)
        pet.add_task(next_task)

    def mark_pending(self) -> None:
        """Set status to pending."""
        self.status = "pending"

    def _next_occurrence_due(self) -> datetime | None:
        """Compute the next due datetime for recurring templates."""
        r = (self.recurrence or "").strip().lower()
        if r == "daily":
            if self.due is not None:
                next_date = self.due.date() + timedelta(days=1)
                t = self.due.time()
            else:
                next_date = date.today() + timedelta(days=1)
                t = datetime.min.time()
            return datetime.combine(next_date, t)
        if r == "weekly":
            if self.due is not None:
                next_date = self.due.date() + timedelta(weeks=1)
                t = self.due.time()
            else:
                next_date = date.today() + timedelta(weeks=1)
                t = datetime.min.time()
            return datetime.combine(next_date, t)
        return None

    def time_sort_key(self) -> tuple[Any, ...]:
        """Sort by clock order: minutes from midnight from ``due`` or ``time_str`` ('HH:MM')."""
        minutes: int | None = None
        if self.due is not None:
            tt = self.due.time()
            minutes = tt.hour * 60 + tt.minute
        elif (self.time_str or "").strip():
            h, m = _hhmm_sort_key(self.time_str)
            if h != 99:
                minutes = h * 60 + m
        if minutes is not None:
            return (0, minutes, self.title)
        return (1, self.title)

    def sort_key(self) -> tuple[Any, ...]:
        """Return sort key: higher priority, shorter duration, then title."""
        return (-self.priority, self.duration_minutes, self.title)

    def instances_for_date(self, target: date) -> list[Task]:
        """Expand recurrence into task instances for the given date."""
        if self.status == "done":
            return []
        r = (self.recurrence or "").strip().lower()
        if r == "daily":
            return [replace(self, status="pending")]
        if r in ("", "once", "none"):
            if self.due is None:
                return [self]
            if self.due.date() == target:
                return [self]
            return []
        if r == "weekly":
            if self.due is None:
                return []
            if target.weekday() == self.due.weekday():
                return [replace(self, status="pending")]
            return []
        return []


def _interval_for_day(task: Task, day: date) -> tuple[datetime, datetime] | None:
    """Return ``(start, end)`` on ``day`` using ``due`` (same calendar date) or ``time_str`` plus ``day``.

    End is ``start + duration`` minutes. Returns ``None`` if the task has no time on ``day`` or if
    ``due`` falls on another date.
    """
    if task.due is not None:
        if task.due.date() != day:
            return None
        start = task.due
    elif (task.time_str or "").strip():
        h, m = _hhmm_sort_key(task.time_str)
        if h == 99:
            return None
        start = datetime.combine(day, datetime.min.time().replace(hour=h, minute=m))
    else:
        return None
    end = start + timedelta(minutes=max(0, task.duration_minutes))
    return (start, end)


class Scheduler:
    """Plans daily care from owner constraints and tasks."""

    def tasks_for_owner(self, owner: Owner) -> list[Task]:
        """Return all tasks from every pet under this owner."""
        return owner.all_tasks()

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return a new list sorted by clock time using ``Task.time_sort_key`` (stable by title)."""
        return sorted(tasks, key=lambda t: t.time_sort_key())

    def filter_tasks(
        self,
        tasks: list[Task],
        *,
        status: str | None = None,
        pet_name: str | None = None,
    ) -> list[Task]:
        """Return tasks whose ``status`` and/or pet ``name`` match when those filters are not ``None``."""
        out: list[Task] = []
        for t in tasks:
            if status is not None and t.status != status:
                continue
            if pet_name is not None and (t.pet is None or t.pet.name != pet_name):
                continue
            out.append(t)
        return out

    def detect_time_overlaps(
        self,
        tasks: list[Task],
        *,
        plan_date: date | None = None,
    ) -> list[str]:
        """Pairwise overlap check on ``plan_date``: pending tasks only; never raises.

        Uses half-open intervals ``[start, end)`` plus a same-``start`` rule. Tasks without a time on
        ``plan_date`` are skipped. Returns human-readable warning strings (empty list if none).
        """
        day = plan_date or date.today()
        annotated: list[tuple[Task, datetime, datetime]] = []
        for t in tasks:
            if t.status == "done":
                continue
            iv = _interval_for_day(t, day)
            if iv is None:
                continue
            start, end = iv
            annotated.append((t, start, end))

        warnings: list[str] = []
        for (t1, s1, e1), (t2, s2, e2) in combinations(annotated, 2):
            overlap = (s1 < e2 and s2 < e1) or (s1 == s2)
            if overlap:
                p1 = t1.pet.name if t1.pet else "?"
                p2 = t2.pet.name if t2.pet else "?"
                warnings.append(
                    f"Time overlap: “{t1.title}” ({p1}, {s1.strftime('%H:%M')}–{e1.strftime('%H:%M')}) "
                    f"and “{t2.title}” ({p2}, {s2.strftime('%H:%M')}–{e2.strftime('%H:%M')})."
                )
        return warnings

    def collect_tasks_for_day(self, owner: Owner, day: date) -> list[Task]:
        """Collect concrete task instances for a calendar day."""
        concrete: list[Task] = []
        for pet in owner.pets:
            for task in pet.tasks:
                concrete.extend(task.instances_for_date(day))
        return concrete

    def build_daily_plan(
        self,
        owner: Owner,
        tasks: list[Task] | None = None,
        *,
        plan_date: date | None = None,
    ) -> tuple[list[Task], list[str]]:
        """Build a greedy daily plan and human-readable notes."""
        day = plan_date or date.today()
        if tasks is None:
            candidates = self.collect_tasks_for_day(owner, day)
        else:
            candidates = list(tasks)

        pending = [t for t in candidates if t.status != "done"]
        pending.sort(key=lambda t: t.sort_key())

        messages: list[str] = []
        planned: list[Task] = []
        used = 0
        budget = owner.available_minutes

        for task in pending:
            d = max(0, task.duration_minutes)
            if used + d <= budget:
                planned.append(task)
                used += d
                messages.append(
                    f"Included “{task.title}” ({d} min, priority {task.priority})."
                )
            else:
                messages.append(
                    f"Skipped “{task.title}” ({d} min) — not enough time remaining "
                    f"({budget - used} min left)."
                )

        if not pending:
            messages.append("No pending tasks for this day.")
        else:
            messages.insert(
                0,
                f"Planning for {day}: {budget} min available; "
                f"scheduled {used} min across {len(planned)} task(s).",
            )

        return planned, messages

    def detect_conflicts(self, owner: Owner, tasks: list[Task] | None = None) -> list[str]:
        """Return messages when pending work exceeds available time."""
        if tasks is None:
            tasks = self.tasks_for_owner(owner)
        total = sum(max(0, t.duration_minutes) for t in tasks if t.status != "done")
        budget = owner.available_minutes
        msgs: list[str] = []
        if total > budget:
            msgs.append(
                f"Total pending task time ({total} min) exceeds available time ({budget} min) "
                f"by {total - budget} min."
            )
        if budget < 0:
            msgs.append("Owner available_minutes is negative (invalid).")
        return msgs
