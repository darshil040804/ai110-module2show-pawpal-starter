"""PawPal+ logic layer: Owner, Pet, Task, and Scheduler."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field, replace
from datetime import date, time, timedelta
from enum import IntEnum
from typing import Optional


class Priority(IntEnum):
    """Numeric so tasks sort correctly (higher value = more important)."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


VALID_FREQUENCIES = ("once", "daily", "weekly")

# How far ahead the next occurrence of a recurring task is due.
RECURRENCE_STEP = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}


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
    due_date: date = field(default_factory=date.today)

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

    def next_occurrence(self) -> Optional[Task]:
        """Return a fresh, incomplete copy due one step after today (or after its due date if that's later), or None for one-off tasks."""
        step = RECURRENCE_STEP.get(self.frequency)
        if step is None:
            return None
        # Counting from today stops an overdue task from spawning another overdue copy.
        start = max(self.due_date, date.today())
        return replace(self, completed=False, due_date=start + step)


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

    def get_pet(self, name: str) -> Optional[Pet]:
        """Return the pet with this name, or None if there isn't one."""
        return next((pet for pet in self.pets if pet.name == name), None)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of the owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """Builds and explains a daily plan from all of an owner's pets' tasks."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.plan: list[Task] = []
        self.explanations: list[str] = []

    # --- Sorting and filtering ----------------------------------------------

    def sort_by_time(self, tasks: Optional[list[Task]] = None) -> list[Task]:
        """Return tasks ordered by due date, then preferred time; untimed tasks go last each day."""
        if tasks is None:
            tasks = self.owner.get_all_tasks()
        return sorted(tasks, key=lambda t: (t.due_date, t.preferred_time or time.max))

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        completed: Optional[bool] = None,
        due_on: Optional[date] = None,
    ) -> list[Task]:
        """Return the owner's tasks matching every filter given (None means "don't filter on this")."""
        return [
            task
            for task in self.owner.get_all_tasks()
            if (pet_name is None or task.pet_name == pet_name)
            and (completed is None or task.completed == completed)
            and (due_on is None or task.due_date == due_on)
        ]

    # --- Recurring tasks ------------------------------------------------------

    def mark_task_complete(self, task: Task) -> Optional[Task]:
        """Complete a task and, if it recurs, add its next occurrence to the same pet (only once)."""
        if task.completed:
            return None  # already handled; don't spawn a duplicate occurrence
        task.mark_complete()
        upcoming = task.next_occurrence()
        if upcoming is not None:
            pet = self.owner.get_pet(task.pet_name)
            if pet is None:
                raise ValueError(f"No pet named '{task.pet_name}' to attach the next occurrence to.")
            pet.add_task(upcoming)
        return upcoming

    # --- Conflict detection ---------------------------------------------------

    def detect_conflicts(self, tasks: Optional[list[Task]] = None) -> list[str]:
        """Return a warning for each time slot shared by two or more pending tasks (exact start-time match)."""
        if tasks is None:
            tasks = self.filter_tasks(completed=False)

        slots: dict[tuple[date, time], list[Task]] = defaultdict(list)
        for task in tasks:
            if task.preferred_time is not None:
                slots[(task.due_date, task.preferred_time)].append(task)

        warnings = []
        for (day, at), clashing in sorted(slots.items()):
            if len(clashing) > 1:
                names = ", ".join(f"{t.title} ({t.pet_name})" for t in clashing)
                warnings.append(f"Conflict on {day} at {at.strftime('%H:%M')}: {names}")
        return warnings

    # --- Planning ---------------------------------------------------------------

    def generate_plan(self, day: Optional[date] = None) -> list[Task]:
        """Rebuild plan and explanations from scratch: pending tasks due by `day`, by priority, within available time."""
        day = day or date.today()
        self.plan = []
        self.explanations = []

        # Read across every pet via the Owner, not from a single pet.
        pending = [
            task for task in self.owner.get_all_tasks()
            if not task.completed and task.due_date <= day
        ]

        def selection_key(task: Task):
            """Sort key: priority, then preference match, then time, then duration."""
            preferred = task.category in self.owner.preferences
            return (-task.priority, not preferred, task.preferred_time or time.max, task.duration_minutes)

        remaining = self.owner.available_minutes
        for task in sorted(pending, key=selection_key):
            label = f"{task.title} ({task.pet_name})"
            if task.duration_minutes <= remaining:
                self.plan.append(task)
                remaining -= task.duration_minutes
                reason = f"priority {task.priority.name.lower()}"
                if task.category in self.owner.preferences:
                    reason += f", matches preference '{task.category}'"
                if task.due_date < day:
                    reason += f", overdue since {task.due_date}"
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
        self.plan = self.sort_by_time(self.plan)
        self.explanations.extend(f"Warning: {w}" for w in self.detect_conflicts(self.plan))
        return self.plan

    def explain_plan(self) -> str:
        """Return a human-readable explanation of why the plan looks the way it does."""
        if not self.explanations:
            return "No plan generated yet (or no pending tasks)."
        return "\n".join(self.explanations)
