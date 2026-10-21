"""Automated tests for the PawPal+ logic layer."""

import sys
from pathlib import Path

# Make pawpal_system importable when running pytest from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date, time, timedelta

import pytest

from pawpal_system import Owner, Pet, Priority, Scheduler, Task

TODAY = date.today()


def make_scheduler(available_minutes=120):
    """Owner with two pets and tasks added out of time order."""
    owner = Owner("Jordan", available_minutes=available_minutes)
    mochi, luna = Pet("Mochi", "dog"), Pet("Luna", "cat")
    owner.add_pet(mochi)
    owner.add_pet(luna)
    mochi.add_task(Task("Evening walk", "exercise", 30, preferred_time=time(18, 0)))
    luna.add_task(Task("Breakfast", "feeding", 10, preferred_time=time(8, 0)))
    mochi.add_task(Task("Play", "enrichment", 15))  # no preferred time
    mochi.add_task(Task("Morning walk", "exercise", 30, preferred_time=time(7, 30)))
    return Scheduler(owner), mochi, luna


# --- Task and Pet basics -------------------------------------------------------


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


@pytest.mark.parametrize(
    "kwargs",
    [
        {"title": "   "},
        {"title": "Walk", "duration_minutes": 0},
        {"title": "Walk", "duration_minutes": -5},
        {"title": "Walk", "frequency": "monthly"},
        {"title": "Walk", "priority": 7},
    ],
)
def test_invalid_task_data_is_rejected(kwargs):
    with pytest.raises(ValueError):
        Task(**kwargs)


def test_edit_updates_fields_and_revalidates():
    task = Task("Walk", duration_minutes=20)

    task.edit(duration_minutes=45, priority=3)

    assert task.duration_minutes == 45
    assert task.priority is Priority.HIGH
    with pytest.raises(ValueError):
        task.edit(duration_minutes=0)


def test_get_all_tasks_combines_every_pet():
    scheduler, _, _ = make_scheduler()

    assert len(scheduler.owner.get_all_tasks()) == 4


# --- Sorting -----------------------------------------------------------------------


def test_sort_by_time_orders_tasks_and_puts_untimed_last():
    scheduler, _, _ = make_scheduler()

    titles = [t.title for t in scheduler.sort_by_time()]

    assert titles == ["Morning walk", "Breakfast", "Evening walk", "Play"]


def test_sort_by_time_orders_by_day_before_time():
    scheduler = Scheduler(Owner("Jordan", 60))
    late_today = Task("Late today", preferred_time=time(22, 0))
    early_tomorrow = Task("Early tomorrow", preferred_time=time(6, 0), due_date=TODAY + timedelta(days=1))

    result = scheduler.sort_by_time([early_tomorrow, late_today])

    assert result == [late_today, early_tomorrow]


def test_sort_by_time_keeps_insertion_order_for_ties():
    scheduler = Scheduler(Owner("Jordan", 60))
    first = Task("First", preferred_time=time(8, 0))
    second = Task("Second", preferred_time=time(8, 0))

    assert scheduler.sort_by_time([first, second]) == [first, second]


def test_sort_by_time_does_not_modify_input():
    scheduler, mochi, _ = make_scheduler()
    original = list(mochi.tasks)

    scheduler.sort_by_time(mochi.tasks)

    assert mochi.tasks == original


def test_sort_by_time_with_no_tasks():
    assert Scheduler(Owner("Jordan", 60)).sort_by_time() == []


# --- Filtering ---------------------------------------------------------------------


def test_filter_tasks_by_pet_and_status():
    scheduler, mochi, _ = make_scheduler()
    mochi.tasks[0].mark_complete()

    assert {t.title for t in scheduler.filter_tasks(pet_name="Luna")} == {"Breakfast"}
    assert [t.title for t in scheduler.filter_tasks(completed=True)] == ["Evening walk"]
    assert len(scheduler.filter_tasks(pet_name="Mochi", completed=False)) == 2


def test_filter_tasks_unknown_pet_returns_empty():
    scheduler, _, _ = make_scheduler()

    assert scheduler.filter_tasks(pet_name="Rex") == []


def test_filter_tasks_with_no_filters_returns_everything():
    scheduler, _, _ = make_scheduler()

    assert len(scheduler.filter_tasks()) == 4


# --- Recurring tasks ---------------------------------------------------------------


def test_completing_daily_task_creates_next_day_occurrence():
    scheduler, mochi, _ = make_scheduler()
    walk = mochi.tasks[0]

    upcoming = scheduler.mark_task_complete(walk)

    assert walk.completed is True
    assert upcoming in mochi.tasks
    assert upcoming.completed is False
    assert upcoming.title == walk.title and upcoming.preferred_time == walk.preferred_time
    assert upcoming.due_date == TODAY + timedelta(days=1)


def test_completing_weekly_task_is_due_in_seven_days():
    task = Task("Brush coat", frequency="weekly")

    assert task.next_occurrence().due_date == TODAY + timedelta(days=7)


def test_completing_one_off_task_does_not_recur():
    scheduler, mochi, _ = make_scheduler()
    vet = Task("Vet visit", frequency="once")
    mochi.add_task(vet)

    assert scheduler.mark_task_complete(vet) is None
    assert len(mochi.tasks) == 4


def test_completing_same_task_twice_creates_only_one_occurrence():
    scheduler, mochi, _ = make_scheduler()
    walk = mochi.tasks[0]

    scheduler.mark_task_complete(walk)
    second = scheduler.mark_task_complete(walk)

    assert second is None
    assert len([t for t in mochi.tasks if t.title == "Evening walk"]) == 2


def test_overdue_daily_task_recurs_from_today_not_from_old_due_date():
    scheduler, mochi, _ = make_scheduler()
    meds = Task("Meds", "medication", 5, due_date=TODAY - timedelta(days=3))
    mochi.add_task(meds)

    upcoming = scheduler.mark_task_complete(meds)

    assert upcoming.due_date == TODAY + timedelta(days=1)


def test_next_occurrence_is_not_in_todays_plan():
    scheduler, mochi, _ = make_scheduler()
    scheduler.mark_task_complete(mochi.tasks[0])

    plan_titles = [t.title for t in scheduler.generate_plan()]

    assert "Evening walk" not in plan_titles


def test_next_occurrence_appears_in_tomorrows_plan():
    scheduler, mochi, _ = make_scheduler()
    scheduler.mark_task_complete(mochi.tasks[0])

    plan = scheduler.generate_plan(day=TODAY + timedelta(days=1))

    assert "Evening walk" in [t.title for t in plan]


# --- Conflict detection ------------------------------------------------------------


def test_detect_conflicts_warns_on_same_time():
    scheduler, mochi, _ = make_scheduler()
    mochi.add_task(Task("Breakfast", "feeding", 10, preferred_time=time(8, 0)))

    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "08:00" in warnings[0]
    assert "Breakfast (Mochi)" in warnings[0] and "Breakfast (Luna)" in warnings[0]


def test_detect_conflicts_same_pet_same_time():
    scheduler, mochi, _ = make_scheduler()
    mochi.add_task(Task("Meds", "medication", 5, preferred_time=time(7, 30)))

    warnings = scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "Morning walk (Mochi)" in warnings[0] and "Meds (Mochi)" in warnings[0]


def test_detect_conflicts_ignores_completed_tasks():
    scheduler, mochi, _ = make_scheduler()
    clash = Task("Breakfast", "feeding", 10, preferred_time=time(8, 0))
    mochi.add_task(clash)
    clash.mark_complete()

    assert scheduler.detect_conflicts() == []


def test_detect_conflicts_ignores_same_time_on_different_days():
    scheduler, mochi, _ = make_scheduler()
    mochi.add_task(Task("Breakfast", preferred_time=time(8, 0), due_date=TODAY + timedelta(days=1)))

    assert scheduler.detect_conflicts() == []


def test_detect_conflicts_ignores_untimed_tasks():
    scheduler, mochi, _ = make_scheduler()
    mochi.add_task(Task("Another untimed task"))

    assert scheduler.detect_conflicts() == []


def test_no_conflicts_without_tasks():
    assert Scheduler(Owner("Jordan", 60)).detect_conflicts() == []


# --- Plan generation ---------------------------------------------------------------


def test_plan_respects_time_budget_and_explains_skips():
    scheduler, _, _ = make_scheduler(available_minutes=40)

    plan = scheduler.generate_plan()

    assert sum(t.duration_minutes for t in plan) <= 40
    assert "Skipped" in scheduler.explain_plan()


def test_plan_prefers_higher_priority_when_time_is_short():
    owner = Owner("Jordan", available_minutes=30)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Grooming", duration_minutes=30, priority=Priority.LOW))
    pet.add_task(Task("Meds", duration_minutes=30, priority=Priority.HIGH))

    plan = Scheduler(owner).generate_plan()

    assert [t.title for t in plan] == ["Meds"]


def test_plan_uses_preference_to_break_priority_ties():
    owner = Owner("Jordan", available_minutes=30, preferences=["exercise"])
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Puzzle toy", "enrichment", 30))
    pet.add_task(Task("Walk", "exercise", 30))

    assert [t.title for t in Scheduler(owner).generate_plan()] == ["Walk"]


def test_plan_fits_task_that_uses_exactly_remaining_time():
    owner = Owner("Jordan", available_minutes=30)
    pet = Pet("Mochi", "dog")
    owner.add_pet(pet)
    pet.add_task(Task("Walk", duration_minutes=30))

    assert len(Scheduler(owner).generate_plan()) == 1


def test_plan_includes_overdue_tasks_and_says_so():
    scheduler, mochi, _ = make_scheduler()
    mochi.add_task(Task("Meds", "medication", 5, due_date=TODAY - timedelta(days=1)))

    plan = scheduler.generate_plan()

    assert "Meds" in [t.title for t in plan]
    assert "overdue" in scheduler.explain_plan()


def test_plan_is_in_time_order():
    scheduler, _, _ = make_scheduler()

    plan = scheduler.generate_plan()

    assert plan == scheduler.sort_by_time(plan)


def test_plan_for_owner_with_no_pets_is_empty():
    scheduler = Scheduler(Owner("Jordan", 60))

    assert scheduler.generate_plan() == []
    assert scheduler.explain_plan() == "No plan generated yet (or no pending tasks)."


def test_plan_for_pet_with_no_tasks_is_empty():
    owner = Owner("Jordan", 60)
    owner.add_pet(Pet("Mochi", "dog"))

    assert Scheduler(owner).generate_plan() == []


def test_plan_with_zero_available_minutes_schedules_nothing():
    scheduler, _, _ = make_scheduler(available_minutes=0)

    assert scheduler.generate_plan() == []


def test_generate_plan_rebuilds_from_scratch():
    scheduler, _, _ = make_scheduler()
    first = list(scheduler.generate_plan())

    second = scheduler.generate_plan()

    assert second == first
    assert len(scheduler.explanations) == len(first)
