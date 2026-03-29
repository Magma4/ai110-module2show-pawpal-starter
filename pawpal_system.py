"""PawPal+ logic layer: domain models and scheduling (skeleton from UML)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class Owner:
    name: str
    available_minutes: int = 0
    preferences: dict[str, Any] = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def register(self) -> None:
        """Persist or validate owner profile (implementation later)."""
        pass

    def register_pet(self, pet: Pet) -> None:
        """Link a pet to this owner and keep both sides consistent."""
        pet.owner = self
        if pet not in self.pets:
            self.pets.append(pet)

    def set_available_time(self, minutes: int) -> None:
        """Set the scheduling time budget for the current day."""
        self.available_minutes = minutes

    def list_pets(self) -> list[Pet]:
        """Return pets managed by this owner."""
        return list(self.pets)


@dataclass
class Pet:
    name: str
    species: str = ""
    owner: Owner | None = None
    notes: str = ""

    def update_profile(self) -> None:
        """Update pet fields from UI or API (implementation later)."""
        pass


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

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.status = "done"

    def sort_key(self) -> tuple[Any, ...]:
        """Return a comparable key for ordering (priority, due time, etc.)."""
        return (-self.priority, self.title)

    def instances_for_date(self, _target: date) -> list[Task]:
        """Expand recurrence into concrete tasks for a given calendar date."""
        return []


class Scheduler:
    """Plans daily care from owner constraints and tasks."""

    def build_daily_plan(
        self, owner: Owner, tasks: list[Task]
    ) -> tuple[list[Task], list[str]]:
        """Return ordered tasks and human-readable explanation lines."""
        pass

    def detect_conflicts(self, owner: Owner, tasks: list[Task]) -> list[str]:
        """Return messages describing scheduling conflicts (e.g., over budget)."""
        pass
