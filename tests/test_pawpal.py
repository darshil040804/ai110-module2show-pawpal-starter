"""Basic tests for the PawPal+ logic layer."""

import sys
from pathlib import Path

# Make pawpal_system importable when running pytest from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import time, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


def test_mark_complete_changes_status():
    task = Task("Morning walk", "exercise", 30)
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Breakfast", "feeding", 10))

    assert len(pet.tasks) == 1
    assert pet.tasks[0].pet_name == "Mochi"


def make_scheduler():
    """Owner with two pets and tasks added out of time order."""
    owner = Owner("Jordan", available_minutes=120)
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    mochi.add_task(Task("Evening walk", "exercise", 30, preferred_time=time(18, 0)))
    luna.add_task(Task("Breakfast", "feeding", 10, preferred_time=time(8, 0)))
    mochi.add_task(Task("Play", "enrichment", 15))  # no preferred time
    mochi.add_task(Task("Morning walk", "exercise", 30, preferred_time=time(7, 30)))
    return Scheduler(owner), mochi, luna


def test_sort_by_time_orders_tasks_and_puts_untimed_last():
    scheduler, _, _ = make_scheduler()

    titles = [t.title for t in scheduler.sort_by_time()]

    assert titles == ["Morning walk", "Breakfast", "Evening walk", "Play"]


def test_filter_tasks_by_pet_and_status():
    scheduler, mochi, _ = make_scheduler()
    mochi.tasks[0].mark_complete()

    assert {t.title for t in scheduler.filter_tasks(pet_name="Luna")} == {"Breakfast"}
    assert [t.title for t in scheduler.filter_tasks(completed=True)] == ["Evening walk"]
    assert len(scheduler.filter_tasks(pet_name="Mochi", completed=False)) == 2


def test_completing_daily_task_creates_next_day_occurrence():
    scheduler, mochi, _ = make_scheduler()
    walk = mochi.tasks[0]

    upcoming = scheduler.mark_task_complete(walk)

    assert walk.completed is True
    assert upcoming in mochi.tasks
    assert upcoming.completed is False
    assert upcoming.due_date == walk.due_date + timedelta(days=1)


def test_completing_weekly_task_is_due_in_seven_days():
    task = Task("Brush coat", frequency="weekly")

    assert task.next_occurrence().due_date == task.due_date + timedelta(days=7)


def test_completing_one_off_task_does_not_recur():
    scheduler, mochi, _ = make_scheduler()
    vet = Task("Vet visit", frequency="once")
    mochi.add_task(vet)

    assert scheduler.mark_task_complete(vet) is None
    assert len(mochi.tasks) == 4


def test_next_occurrence_is_not_in_todays_plan():
    scheduler, mochi, _ = make_scheduler()
    scheduler.mark_task_complete(mochi.tasks[0])

    plan_titles = [t.title for t in scheduler.generate_plan()]

    assert "Evening walk" not in plan_titles


def test_detect_conflicts_warns_on_same_time():
    scheduler, mochi, _ = make_scheduler()
    mochi.add_task(Task("Breakfast", "feeding", 10, preferred_time=time(8, 0)))

    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "08:00" in warnings[0]
    assert "Breakfast (Mochi)" in warnings[0] and "Breakfast (Luna)" in warnings[0]


def test_detect_conflicts_ignores_completed_tasks():
    scheduler, mochi, luna = make_scheduler()
    clash = Task("Breakfast", "feeding", 10, preferred_time=time(8, 0))
    mochi.add_task(clash)
    clash.mark_complete()

    assert scheduler.detect_conflicts() == []
