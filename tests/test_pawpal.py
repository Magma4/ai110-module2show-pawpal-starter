"""Tests for PawPal+ domain logic."""

from pawpal_system import Owner, Pet, Task


def test_mark_complete_sets_status_to_done():
    """Task completion: mark_complete() updates status."""
    task = Task("Morning walk", status="pending")
    task.mark_complete()
    assert task.status == "done"


def test_add_task_increases_pet_task_count():
    """Task addition: add_task appends to the pet's task list."""
    pet = Pet("Luna")
    assert len(pet.tasks) == 0
    task = Task("Feed")
    pet.add_task(task)
    assert len(pet.tasks) == 1
    assert pet.tasks[0] is task
    assert task.pet is pet
