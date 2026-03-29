"""PawPal+ logic layer: domain models and scheduling."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from typing import Any


@dataclass
class Owner:
    name: str
    available_minutes: int = 0
    preferences: dict[str, Any] = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def register(self) -> None:
        """Validate owner profile (extend later for persistence)."""
        if not str(self.name).strip():
            raise ValueError("Owner name cannot be empty")

    def register_pet(self, pet: Pet) -> None:
        """Link a pet to this owner and keep both sides consistent."""
        pet.owner = self
        if pet not in self.pets:
            self.pets.append(pet)

    def set_available_time(self, minutes: int) -> None:
        """Set the scheduling time budget for the current day."""
        if minutes < 0:
            raise ValueError("available_minutes cannot be negative")
        self.available_minutes = minutes

    def list_pets(self) -> list[Pet]:
        """Return pets managed by this owner."""
        return list(self.pets)

    def all_tasks(self) -> list[Task]:
        """All tasks attached to this owner's pets (pet order, then task order)."""
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
        """Update allowed fields from keyword arguments."""
        allowed = {"name", "species", "notes"}
        for key, value in kwargs.items():
            if key in allowed:
                setattr(self, key, value)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet; removes it from another pet if needed."""
        if task.pet is not None and task.pet is not self:
            task.pet.remove_task(task)
        task.pet = self
        if task not in self.tasks:
            self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Detach a task from this pet."""
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
    recurrence: str = ""
    status: str = "pending"

    @property
    def frequency(self) -> str:
        """Alias for recurrence (how often the task repeats)."""
        return self.recurrence

    @frequency.setter
    def frequency(self, value: str) -> None:
        self.recurrence = value

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.status = "done"

    def mark_pending(self) -> None:
        """Mark this task as not yet done."""
        self.status = "pending"

    def sort_key(self) -> tuple[Any, ...]:
        """Comparable key: higher priority first, then shorter duration, then title."""
        return (-self.priority, self.duration_minutes, self.title)

    def instances_for_date(self, target: date) -> list[Task]:
        """Concrete tasks that apply on ``target`` (handles recurrence)."""
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


class Scheduler:
    """Plans daily care from owner constraints and tasks."""

    def tasks_for_owner(self, owner: Owner) -> list[Task]:
        """Flatten all tasks from every pet belonging to ``owner``."""
        return owner.all_tasks()

    def collect_tasks_for_day(self, owner: Owner, day: date) -> list[Task]:
        """Expand each stored task into zero or more instances for ``day``."""
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
        """Return ordered tasks that fit ``owner.available_minutes`` and explanation lines."""
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
        """Describe conflicts such as total work exceeding available time."""
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
