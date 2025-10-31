import os
import csv
import shutil
import pytest
import jora


@pytest.fixture(autouse=True)
def clean_jora_dir():
    """
    Fixture to ensure we start with a clean JORA directory
    before each test and remove it afterward.
    """
    # If a JORA directory exists, back it up
    if os.path.exists("JORA"):
        shutil.rmtree("JORA")

    # Run jora.setup() to create fresh CSV files
    jora.setup()
    yield

    # Cleanup after test
    if os.path.exists("JORA"):
        shutil.rmtree("JORA")


def test_setup():
    """Verify that setup() creates all required CSV files."""
    assert os.path.exists("JORA/OPEN.csv")
    assert os.path.exists("JORA/IN_PROGRESS.csv")
    assert os.path.exists("JORA/CLOSED.csv")

    # Verify the headers are correct
    with open("JORA/OPEN.csv", "r", newline="") as f:
        header = f.readline().strip()
    assert header == "Title,Priority,Description,ID"


def test_create_task():
    """Test that create_task() correctly adds new rows to OPEN.csv."""
    # Add several tasks
    data = [
        ("test", 0, "test0", 1),
        ("test", 1, "test1", 2),
        ("test", 2, "test2", 3),
    ]
    for title, priority, description, count in data:
        jora.create_task(title, priority, description, count)

    # Verify the results
    with open("JORA/OPEN.csv", "r", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    # First row is header; there should be 3 data rows after it
    assert len(rows) == 4

    # Check last row values
    last = rows[-1]
    assert last[0] == "test"
    assert last[1] == "2"
    assert last[2] == "test2"
    assert last[3].isdigit()


def test_create_task_increments_id():
    """Ensure task count increments properly when multiple entries are added."""
    jora.create_task("A", 1, "desc1", 0)
    jora.create_task("B", 2, "desc2", 0)

    with open("JORA/OPEN.csv", "r", newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)

    # Expect header + 2 rows
    assert len(rows) == 3

    # Check IDs are unique and sequential
    ids = [int(row[3]) for row in rows[1:]]
    assert ids == [1, 2]

def test_move_task():
    # Step 1: Create a task in OPEN.csv
    jora.create_task("MoveMe", 1, "Test moving a task", 1)

    # Verify the task exists in OPEN.csv
    with open("JORA/OPEN.csv", "r", newline="") as f:
        reader = list(csv.reader(f))
        assert len(reader) == 2  # header + 1 data row
        task_id = reader[1][3]  # grab the ID of the created task

    # Step 2: Move the task to IN_PROGRESS
    jora.move_task(task_id, "OPEN", "IN_PROGRESS")

    # Step 3: Verify it was removed from OPEN.csv
    with open("JORA/OPEN.csv", "r", newline="") as f:
        reader = list(csv.reader(f))
        # only header should remain
        assert len(reader) == 1

    # Step 4: Verify it now exists in IN_PROGRESS.csv
    with open("JORA/IN_PROGRESS.csv", "r", newline="") as f:
        reader = list(csv.reader(f))
        assert len(reader) == 2  # header + 1 moved row
        moved_row = reader[1]
        assert moved_row[0] == "MoveMe"
        assert moved_row[1] == "1"
        assert moved_row[2] == "Test moving a task"
        assert moved_row[3] == task_id  # ID should be identical
