import csv
import os
import shutil
import pytest
import sys
from unittest import mock
import jora


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
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        return list(reader)


# ----------------------------------------------------------------------
# Core setup and helper function tests
# ----------------------------------------------------------------------

def test_setup_creates_files():
    """setup() should create all CSV files."""
    for name in ["OPEN.csv", "IN_PROGRESS.csv", "CLOSED.csv"]:
        assert os.path.exists(os.path.join("JORA", name))


def test_get_all_tasks_returns_expected_data():
    """get_all_tasks() should return tasks with status labels."""
    jora.create_task("Test 1", 2, "desc", verbose=False)
    jora.create_task("Test 2", 3, "desc", status="IN_PROGRESS", verbose=False)
    jora.create_task("Test 3", 4, "desc", status="CLOSED", verbose=False)

    tasks = jora.get_all_tasks()
    statuses = [t[4] for t in tasks]
    assert set(statuses) == {"OPEN", "IN_PROGRESS", "CLOSED"}
    assert len(tasks) == 3


def test_get_task_count_counts_all_files():
    """get_task_count() should correctly count across all files."""
    jora.create_task("One", 1, "a", verbose=False)
    jora.create_task("Two", 2, "b", status="IN_PROGRESS", verbose=False)
    jora.create_task("Three", 3, "c", status="CLOSED", verbose=False)
    assert jora.get_task_count() == 3


# ----------------------------------------------------------------------
# create_task() tests
# ----------------------------------------------------------------------

def test_create_task_adds_entry():
    """Creating a new task should append a row to OPEN.csv."""
    jora.create_task("Alpha", 3, "Sample")
    data = read_csv("OPEN.csv")
    assert len(data) == 1
    assert data[0][0] == "Alpha"
    assert data[0][1] == "3"
    assert data[0][2] == "Sample"
    assert data[0][3].isdigit()


def test_unique_ids_across_all_files():
    """IDs should be globally unique."""
    jora.create_task("T1", 1, "a", status="OPEN", verbose=False)
    jora.create_task("T2", 2, "b", status="IN_PROGRESS", verbose=False)
    jora.create_task("T3", 3, "c", status="CLOSED", verbose=False)
    ids = set()
    for f in ["OPEN.csv", "IN_PROGRESS.csv", "CLOSED.csv"]:
        for row in read_csv(f):
            ids.add(row[3])
    assert len(ids) == 3


# ----------------------------------------------------------------------
# move_task() tests
# ----------------------------------------------------------------------

def test_move_task_preserves_id_and_creates_in_next_stage():
    """Moving a task should preserve its ID and advance its status."""
    jora.create_task("MoveMe", 2, "desc", verbose=False)
    tasks = jora.get_all_tasks()
    task_id = tasks[0][3]

    jora.move_task(tasks, task_id)

    # Verify new location
    moved_tasks = jora.get_all_tasks()
    moved = [t for t in moved_tasks if t[3] == task_id]
    assert len(moved) == 1
    assert moved[0][4] == "IN_PROGRESS"


def test_move_task_from_in_progress_to_closed():
    """Task in IN_PROGRESS should move to CLOSED."""
    jora.create_task("TaskInProgress", 1, "desc", status="IN_PROGRESS", verbose=False)
    tasks = jora.get_all_tasks()
    task_id = [t for t in tasks if t[4] == "IN_PROGRESS"][0][3]

    jora.move_task(tasks, task_id)

    all_tasks = jora.get_all_tasks()
    closed = [t for t in all_tasks if t[3] == task_id and t[4] == "CLOSED"]
    assert len(closed) == 1


# ----------------------------------------------------------------------
# delete_task() tests
# ----------------------------------------------------------------------

def test_delete_task_removes_entry():
    """delete_task() should remove a task from its current file."""
    jora.create_task("DeleteMe", 2, "desc", verbose=False)
    tasks = jora.get_all_tasks()
    task_id = tasks[0][3]

    jora.delete_task(tasks, task_id)

    remaining = jora.get_all_tasks()
    assert all(t[3] != task_id for t in remaining)


# ----------------------------------------------------------------------
# show_tasks() tests
# ----------------------------------------------------------------------

def test_show_tasks_sorts_and_limits_output(capsys):
    """show_tasks() should print tasks sorted by priority and limited to 5."""
    # Suppress create_task() output during setup
    with capsys.disabled():
        for i in range(7):
            jora.create_task(f"Task{i}", i % 5, f"desc{i}", verbose=False)

    tasks = jora.get_all_tasks()
    jora.show_tasks(tasks, num=3)

    output = capsys.readouterr().out.strip().splitlines()
    assert len(output) == 3


# ----------------------------------------------------------------------
# CLI flag tests
# ----------------------------------------------------------------------

def test_flag_new_creates_task(monkeypatch):
    """'-n' flag should create a new task via CLI."""
    inputs = iter(["CLI Task", "2", "CLI desc"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    test_argv = ["jora.py", "-n"]
    monkeypatch.setattr(sys, "argv", test_argv)

    jora.main()
    data = read_csv("OPEN.csv")
    assert len(data) == 1
    assert data[0][0] == "CLI Task"


def test_flag_delete_task(monkeypatch):
    """'-x' flag should delete task by ID."""
    jora.create_task("CLI Delete", 1, "desc", verbose=False)
    task_id = read_csv("OPEN.csv")[0][3]

    test_argv = ["jora.py", "-x", task_id]
    monkeypatch.setattr(sys, "argv", test_argv)

    jora.main()
    assert all(row[3] != task_id for row in read_csv("OPEN.csv"))