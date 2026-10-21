"""Temporary testing ground: build a small household and print today's schedule."""

import sys
from datetime import time

from pawpal_system import Owner, Pet, Priority, Scheduler, Task


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # so the em dash prints on Windows consoles
    owner = Owner("Jordan", available_minutes=90, preferences=["exercise"])

    mochi = Pet("Mochi", "dog", age=3)
    luna = Pet("Luna", "cat", age=5)
    owner.add_pet(mochi)
    owner.add_pet(luna)

    mochi.add_task(Task("Morning walk", "exercise", 30, Priority.HIGH, time(7, 30)))
    mochi.add_task(Task("Evening walk", "exercise", 30, Priority.MEDIUM, time(18, 0)))
    luna.add_task(Task("Breakfast", "feeding", 10, Priority.HIGH, time(8, 0)))
    luna.add_task(Task("Litter box", "hygiene", 10, Priority.MEDIUM, time(12, 0)))
    luna.add_task(Task("Brush coat", "grooming", 20, Priority.LOW, time(20, 0), frequency="weekly"))

    scheduler = Scheduler(owner)
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


if __name__ == "__main__":
    main()
