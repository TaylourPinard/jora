'''
Pytest testing suite for jora.py, only works when jora.py is present, 
when jora is being run as a script this is incompatible
'''

import csv
import sys
import os
import shutil
import pytest
import jora

# ----------------------------------------------------------------------
# Fixture to clean up JORA directory before/after tests
# ----------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_jora_dir():
    """Ensure a fresh JORA directory before and after every test."""
    if os.path.exists("JORA"):
        shutil.rmtree("JORA")
    jora.setup()
    yield
    if os.path.exists("JORA"):
        shutil.rmtree("JORA")


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------

def read_csv(file_name):
    """Read all rows excluding header."""
    path = os.path.join("JORA", file_name)
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)
        return list(reader)


# ----------------------------------------------------------------------
# Core CRUD Tests
# ----------------------------------------------------------------------

def test_create_task_adds_entry():
    """Creating a task adds it to tasks dict and CSV."""
    tasks = jora.load_tasks_dict()
    jora.create_task(tasks, "Test Task", 3, "Description")
    tasks = jora.load_tasks_dict()

    # There should be exactly 1 task
    assert len(tasks) == 1
    tid = list(tasks.keys())[0]
    t = tasks[tid]
    assert t["title"] == "Test Task"
    assert t["priority"] == 3
    assert t["description"] == "Description"
    assert t["status"] == "OPEN"

    # Check CSV
    data = read_csv("OPEN.csv")
    assert len(data) == 1
    assert data[0][3] == tid


def test_unique_ids_across_files():
    """IDs should be globally unique across all statuses."""
    tasks = jora.load_tasks_dict()
    jora.create_task(tasks, "Task1", 1, "A")
    jora.create_task(tasks, "Task2", 2, "B")
    jora.create_task(tasks, "Task3", 3, "C")

    tids = list(tasks.keys())
    assert len(tids) == len(set(tids))


def test_move_task_preserves_id_and_creates_in_next_stage():
    """Move task to next stage and preserve its ID."""
    tasks = jora.load_tasks_dict()
    jora.create_task(tasks, "MoveMe", 2, "desc")
    tid = list(tasks.keys())[0]

    jora.move_task(tasks, tid)
    tasks = jora.load_tasks_dict()
    assert tasks[tid]["status"] == "IN_PROGRESS"

    jora.move_task(tasks, tid)
    tasks = jora.load_tasks_dict()
    assert tasks[tid]["status"] == "CLOSED"


def test_delete_task_removes_entry():
    """Delete task by ID removes it from dict and CSV."""
    tasks = jora.load_tasks_dict()
    jora.create_task(tasks, "DeleteMe", 1, "desc")
    tid = list(tasks.keys())[0]

    jora.delete_task(tasks, tid)
    tasks = jora.load_tasks_dict()
    assert tid not in tasks
    assert not read_csv("OPEN.csv")


def test_show_tasks_sorts_and_limits_output(capsys):
    """show_tasks() prints top N tasks by priority."""
    tasks = jora.load_tasks_dict()
    for i in range(7):
        jora.create_task(tasks, f"Task{i}", i % 5, f"desc{i}", False)
    tasks = jora.load_tasks_dict()

    jora.show_tasks(tasks, num=3)
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 3
    # Highest priority first
    priorities = [int(line.split("Priority: ")[1].split(",")[0]) for line in out]
    assert priorities == sorted(priorities, reverse=True)


# ----------------------------------------------------------------------
# CLI flag tests
# ----------------------------------------------------------------------

def test_flag_new_creates_task(monkeypatch):
    """Test that '-n' creates a task via CLI."""
    inputs = iter(["CLI Task", "2", "desc"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    monkeypatch.setattr(sys, "argv", ["jora.py", "-n"])

    jora.main()
    tasks = jora.load_tasks_dict()
    assert any(t["title"] == "CLI Task" for t in tasks.values())


def test_flag_delete_task(monkeypatch):
    """Test deleting a task via '-x' CLI flag."""
    tasks = jora.load_tasks_dict()
    jora.create_task(tasks, "ToDelete", 1, "desc")
    tid = list(tasks.keys())[0]

    monkeypatch.setattr(sys, "argv", ["jora.py", "-x", tid])
    jora.main()

    tasks = jora.load_tasks_dict()
    assert tid not in tasks


def test_flag_move_task(monkeypatch):
    """Test moving a task via '-mv' CLI flag."""
    tasks = jora.load_tasks_dict()
    jora.create_task(tasks, "ToMove", 2, "desc")
    tid = list(tasks.keys())[0]

    monkeypatch.setattr(sys, "argv", ["jora.py", "-mv", tid])
    jora.main()
    tasks = jora.load_tasks_dict()
    assert tasks[tid]["status"] == "IN_PROGRESS"


def test_show_id_flag(capsys):
    """Test showing task by ID via '-id' flag."""
    tasks = jora.load_tasks_dict()
    jora.create_task(tasks, "TaskShowID", 3, "desc")
    tid = list(tasks.keys())[0]

    sys.argv = ["jora.py", "-id", tid]
    jora.main()
    out = capsys.readouterr().out
    assert "TaskShowID" in out
    assert "Priority: 3" in out
    assert "Status: OPEN" in out
