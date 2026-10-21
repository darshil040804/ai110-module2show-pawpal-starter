"""Temporary testing ground: build a small household and print today's schedule."""

import sys
from datetime import time

from pawpal_system import Owner, Pet, Priority, Scheduler, Task


def print_tasks(heading: str, tasks: list[Task]) -> None:
    """Print a heading and one line per task."""
    print(heading)
    if not tasks:
        print("  (none)")
    for task in tasks:
        when = task.preferred_time.strftime("%H:%M") if task.preferred_time else "Anytime"
        status = "done" if task.completed else "pending"
        print(f"  {task.due_date} {when} — {task.title} ({task.pet_name}, {task.frequency}, {status})")
    print()


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # so the em dash prints on Windows consoles
    owner = Owner("Jordan", available_minutes=90, preferences=["exercise"])

    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    # Added deliberately out of time order to exercise sort_by_time().
    mochi.add_task(Task("Evening walk", "exercise", 30, Priority.MEDIUM, time(18, 0)))
    luna.add_task(Task("Brush coat", "grooming", 20, Priority.LOW, time(20, 0), frequency="weekly"))
    luna.add_task(Task("Litter box", "hygiene", 10, Priority.MEDIUM, time(12, 0)))
    mochi.add_task(Task("Morning walk", "exercise", 30, Priority.HIGH, time(7, 30)))
    luna.add_task(Task("Breakfast", "feeding", 10, Priority.HIGH, time(8, 0)))
    # Same time as Luna's breakfast, to trigger a conflict warning.
    mochi.add_task(Task("Breakfast", "feeding", 10, Priority.HIGH, time(8, 0)))

    scheduler = Scheduler(owner)

    print_tasks("All tasks (as added):", owner.get_all_tasks())
    print_tasks("Sorted by time:", scheduler.sort_by_time())
    print_tasks("Luna's tasks only:", scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Luna")))

    print("Conflict check:")
    for warning in scheduler.detect_conflicts() or ["  No conflicts."]:
        print(f"  {warning}")
    print()

    # Completing a recurring task schedules its next occurrence automatically.
    morning_walk = next(t for t in mochi.tasks if t.title == "Morning walk")
    upcoming = scheduler.mark_task_complete(morning_walk)
    print(f"Completed '{morning_walk.title}'; next one due {upcoming.due_date}.\n")
    print_tasks("Completed tasks:", scheduler.filter_tasks(completed=True))
    print_tasks("Mochi's pending tasks:", scheduler.sort_by_time(scheduler.filter_tasks(pet_name="Mochi", completed=False)))

    plan = scheduler.generate_plan()
    print("Today's Schedule\n")
    for pet in owner.pets:
        print(f"Daily plan for {pet.name} ({pet.species.title()}):")
        pet_tasks = [task for task in plan if task.pet_name == pet.name]
        if not pet_tasks:
            print("  (nothing scheduled)")
        for task in pet_tasks:
            when = task.preferred_time.strftime("%H:%M") if task.preferred_time else "Anytime"
            print(
                f"  {when} — {task.title} ({task.duration_minutes} min) "
                f"[priority: {task.priority.name.lower()}]"
            )
        print()

    print("Why this plan:")
    print(scheduler.explain_plan())


if __name__ == "__main__":
    main()
