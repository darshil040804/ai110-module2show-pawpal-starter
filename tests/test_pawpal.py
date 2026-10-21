"""Basic tests for the PawPal+ logic layer."""

import sys
from pathlib import Path

# Make pawpal_system importable when running pytest from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pawpal_system import Pet, Task


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
