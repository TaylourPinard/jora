import csv
import os
import shutil
import pytest
import jora


@pytest.fixture(autouse=True)
def clean_jora_dir():
    """
    Automatically run before and after every test.
    Ensures a fresh JORA directory for isolation.
    """
    if os.path.exists("JORA"):
        shutil.rmtree("JORA")
    jora.setup()
    yield
    if os.path.exists("JORA"):
        shutil.rmtree("JORA")


def read_csv(file_name):
    """Helper to read all data rows (excluding header) from a JORA CSV."""
    path = os.path.join("JORA", file_name)
    with open(path, newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        return list(reader)


# ----------------------------------------------------------------------
# Core Setup Tests
# ----------------------------------------------------------------------

def test_setup_creates_files():
    """Ensure setup() creates all required CSV files."""
    for name in ["OPEN.csv", "IN_PROGRESS.csv", "CLOSED.csv"]:
        assert os.path.exists(os.path.join("JORA", name))


# ----------------------------------------------------------------------
# create_task Tests
# ----------------------------------------------------------------------

def test_create_task_adds_entry():
    """Verify that creating a new task adds a row to OPEN.csv."""
    jora.create_task("Test Task", 3, "This is a test")
    data = read_csv("OPEN.csv")
    assert len(data) == 1
    assert data[0][0] == "Test Task"
    assert data[0][1] == "3"
    assert data[0][2] == "This is a test"
    assert data[0][3].isdigit()


def test_multiple_tasks_have_unique_ids():
    """Ensure each new task receives a unique ID globally."""
    jora.create_task("Alpha", 1, "First")
    jora.create_task("Bravo", 2, "Second")
    jora.create_task("Charlie", 3, "Third")

    ids = {row[3] for row in read_csv("OPEN.csv")}
    assert len(ids) == 3  # all IDs must be unique


# ----------------------------------------------------------------------
# move_task Tests
# ----------------------------------------------------------------------

def test_move_task_preserves_id():
    """Moving a task should keep its original ID and remove it from source."""
    jora.create_task("Movable Task", 2, "To be moved")

    open_data = read_csv("OPEN.csv")
    task_id = open_data[0][3]

    jora.move_task(task_id, "OPEN", "IN_PROGRESS")

    open_data = read_csv("OPEN.csv")
    in_progress_data = read_csv("IN_PROGRESS.csv")

    # Source should be empty (just header)
    assert len(open_data) == 0
    # Destination should contain the moved task with same ID
    assert len(in_progress_data) == 1
    assert in_progress_data[0][3] == task_id


# ----------------------------------------------------------------------
# get_task_count Tests
# ----------------------------------------------------------------------

def test_get_task_count_counts_all_files():
    """get_task_count() should count tasks across all status files."""
    jora.create_task("Task 1", 1, "desc1")
    jora.create_task("Task 2", 2, "desc2", status="IN_PROGRESS")
    jora.create_task("Task 3", 3, "desc3", status="CLOSED")

    total = jora.get_task_count()
    assert total == 3


# ----------------------------------------------------------------------
# Cross-file Uniqueness Tests
# ----------------------------------------------------------------------

def test_ids_are_unique_across_all_files():
    """IDs must never repeat across any stage."""
    jora.create_task("OpenTask", 1, "Open", status="OPEN")
    jora.create_task("ProgressTask", 2, "InProgress", status="IN_PROGRESS")
    jora.create_task("ClosedTask", 3, "Closed", status="CLOSED")

    ids = set()
    for name in ["OPEN.csv", "IN_PROGRESS.csv", "CLOSED.csv"]:
        for row in read_csv(name):
            ids.add(row[3])

    assert len(ids) == 3  # all IDs globally unique

import os
import csv
import shutil
import pytest
from unittest import mock
import jora
import sys

@pytest.fixture(autouse=True)
def clean_jora_dir():
    """Ensure a fresh JORA directory before and after every test."""
    if os.path.exists("JORA"):
        shutil.rmtree("JORA")
    jora.setup()
    yield
    if os.path.exists("JORA"):
        shutil.rmtree("JORA")


def read_csv(file_name):
    """Helper to read all data rows (excluding header) from a JORA CSV."""
    path = os.path.join("JORA", file_name)
    with open(path, newline="") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        return list(reader)


# ----------------------------------------------------------------------
# CLI Flag Tests
# ----------------------------------------------------------------------

def test_flag_new_creates_task(monkeypatch):
    """Test that '-n' flag triggers new task creation."""
    # Simulate user input for title, priority, description
    inputs = iter(["Test CLI Task", "2", "CLI description"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    # Mock argv to include the -n flag
    test_argv = ["jora.py", "-n"]
    monkeypatch.setattr(sys, "argv", test_argv)

    # Run main
    jora.main()

    # Assert task was added to OPEN.csv
    data = read_csv("OPEN.csv")
    assert len(data) == 1
    assert data[0][0] == "Test CLI Task"
    assert data[0][1] == "2"
    assert data[0][2] == "CLI description"


def test_flag_move_task(monkeypatch):
    """Test that '-mv' flag moves a task from one file to another."""
    # Create a task first
    jora.create_task("Movable", 1, "to move")
    task_id = read_csv("OPEN.csv")[0][3]

    # Mock argv to include -mv flag
    test_argv = ["jora.py", "-mv", task_id, "OPEN", "IN_PROGRESS"]
    monkeypatch.setattr(sys, "argv", test_argv)

    # Run main
    jora.main()

    # Verify task moved
    assert len(read_csv("OPEN.csv")) == 0
    in_progress_data = read_csv("IN_PROGRESS.csv")
    assert len(in_progress_data) == 1
    assert in_progress_data[0][3] == task_id

def test_delete_task():
    """
    Test deleting a task by ID using the -x flag.
    Will fail until delete_task() is implemented.
    """
    # First, create a task
    jora.create_task("Task to Delete", 1, "This task will be deleted")
    task_id = read_csv("OPEN.csv")[0][3]

    # Simulate running delete_task via the -x flag
    test_argv = ["jora.py", "-x", task_id]
    with mock.patch.object(sys, "argv", test_argv):
        jora.main()

    # Check that the task no longer exists in OPEN.csv
    data = read_csv("OPEN.csv")
    assert all(row[3] != task_id for row in data), "Task was not deleted"

def test_flag_delete_task(monkeypatch):
    """
    Test that the '-x' delete flag removes a task by ID via the CLI.
    """
    # First, create a task
    jora.create_task("Task to Delete via CLI", 1, "CLI deletion test")
    task_id = read_csv("OPEN.csv")[0][3]

    # Simulate running the script with -x <task_id>
    test_argv = ["jora.py", "-x", task_id]
    monkeypatch.setattr(sys, "argv", test_argv)

    # Run main (delete should happen)
    jora.main()

    # Check that the task no longer exists
    data = read_csv("OPEN.csv")
    assert all(row[3] != task_id for row in data), "Task was not deleted via -x flag"
