"""PawPal+ logic layer: Owner, Pet, Task, and Scheduler (skeleton only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from enum import IntEnum
from typing import Optional


class Priority(IntEnum):
    """Numeric so tasks sort correctly (higher value = more important)."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


@dataclass
class Task:
    title: str
    category: str = "general"
    duration_minutes: int = 15
    priority: Priority = Priority.MEDIUM
    preferred_time: Optional[time] = None
    completed: bool = False
    pet_name: str = ""  # set by Pet.add_task so the plan can say who the task is for

    def __post_init__(self) -> None:
        """Reject invalid data before the scheduler ever sees it."""
        pass

    def mark_complete(self) -> None:
        """Mark this task as done."""
        pass

    def edit(self, **changes) -> None:
        """Update task fields (title, duration, priority, ...)."""
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet and tag it with this pet's name."""
        pass

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet."""
        pass

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that are not yet completed."""
        pass


class Owner:
    def __init__(
        self,
        name: str,
        available_minutes: int,
        preferences: Optional[list[str]] = None,
    ) -> None:
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences or []
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        pass

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner."""
        pass

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of the owner's pets."""
        pass


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.plan: list[Task] = []
        self.explanations: list[str] = []

    def generate_plan(self) -> list[Task]:
        """Rebuild plan and explanations from scratch: pending tasks by priority within available time."""
        pass

    def explain_plan(self) -> str:
        """Return a human-readable explanation of why the plan looks the way it does."""
        pass
