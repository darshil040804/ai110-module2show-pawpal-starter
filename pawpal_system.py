"""PawPal+ logic layer: Owner, Pet, Task, and Scheduler."""

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


VALID_FREQUENCIES = ("once", "daily", "weekly")


@dataclass
class Task:
    """A single care activity for one pet."""

    title: str
    category: str = "general"
    duration_minutes: int = 15
    priority: Priority = Priority.MEDIUM
    preferred_time: Optional[time] = None
    frequency: str = "daily"
    completed: bool = False
    pet_name: str = ""  # set by Pet.add_task so the plan can say who the task is for

    def __post_init__(self) -> None:
        """Reject invalid data before the scheduler ever sees it."""
        if not self.title.strip():
            raise ValueError("Task title cannot be empty.")
        if self.duration_minutes <= 0:
            raise ValueError("Task duration must be a positive number of minutes.")
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(f"Frequency must be one of {VALID_FREQUENCIES}.")
        # Accept plain ints (1-3) as well as Priority members.
        self.priority = Priority(self.priority)

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def edit(self, **changes) -> None:
        """Update task fields (title, duration, priority, ...)."""
        for name, value in changes.items():
            if not hasattr(self, name):
                raise AttributeError(f"Task has no field '{name}'.")
            setattr(self, name, value)
        self.__post_init__()  # re-validate after changes


@dataclass
class Pet:
    """A pet's profile and the care tasks it needs."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a care task to this pet and tag it with this pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a care task from this pet."""
        self.tasks.remove(task)

    def get_pending_tasks(self) -> list[Task]:
        """Return tasks that are not yet completed."""
        return [task for task in self.tasks if not task.completed]


class Owner:
    """The pet owner: their time budget, preferences, and pets."""

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
        if pet in self.pets:
            raise ValueError(f"{pet.name} is already registered.")
        self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from this owner."""
        self.pets.remove(pet)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of the owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """Builds and explains a daily plan from all of an owner's pets' tasks."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.plan: list[Task] = []
        self.explanations: list[str] = []

    @staticmethod
    def _time_sort_key(task: Task) -> time:
        """Tasks with no preferred time go to the end of the day."""
        return task.preferred_time or time.max

    def generate_plan(self) -> list[Task]:
        """Rebuild plan and explanations from scratch: pending tasks by priority within available time."""
        self.plan = []
        self.explanations = []

        # Read across every pet via the Owner, not from a single pet.
        pending = [task for task in self.owner.get_all_tasks() if not task.completed]

        # Highest priority first; preferred categories break ties, then earlier time, then shorter.
        def selection_key(task: Task):
            """Sort key: priority, then preference match, then time, then duration."""
            preferred = task.category in self.owner.preferences
            return (-task.priority, not preferred, self._time_sort_key(task), task.duration_minutes)

        remaining = self.owner.available_minutes
        for task in sorted(pending, key=selection_key):
            label = f"{task.title} ({task.pet_name})"
            if task.duration_minutes <= remaining:
                self.plan.append(task)
                remaining -= task.duration_minutes
                reason = f"priority {task.priority.name.lower()}"
                if task.category in self.owner.preferences:
                    reason += f", matches preference '{task.category}'"
                self.explanations.append(
                    f"Scheduled {label}: {reason}, {task.duration_minutes} min "
                    f"({remaining} min left)."
                )
            else:
                self.explanations.append(
                    f"Skipped {label}: needs {task.duration_minutes} min but only "
                    f"{remaining} min left."
                )

        # Present the chosen tasks in the order they happen during the day.
        self.plan.sort(key=self._time_sort_key)
        return self.plan

    def explain_plan(self) -> str:
        """Return a human-readable explanation of why the plan looks the way it does."""
        if not self.explanations:
            return "No plan generated yet (or no pending tasks)."
        return "\n".join(self.explanations)
