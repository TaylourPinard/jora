#!/usr/bin/env python3
"""
Jora - CLI Jira-style ticket tracker
Uses CSV files as source of truth and keeps a dictionary cache for fast lookups.
"""

import csv
import sys
import argparse
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--new", action="store_true", help="create a new task")
    parser.add_argument("-mv", "--move", nargs=1, help="move a task. usage '-mv <id>'")
    parser.add_argument("-x", "--delete", nargs=1, help="delete a task")
    parser.add_argument("-s", "--show", nargs=1, help="number of tasks to show")
    parser.add_argument("-id", "--show-id", nargs=1, help="show task by ID")

    args = parser.parse_args()

    if not os.path.exists("JORA"):
        setup()

    tasks = load_tasks_dict()

    if len(sys.argv) == 1:
        if tasks:
            show_tasks(tasks)
        else:
            title, priority, description = get_task_parameters()
            create_task(tasks, title, priority, description)

    if args.new:
        title, priority, description = get_task_parameters()
        create_task(tasks, title, priority, description)

    if args.move:
        move_task(tasks, args.move[0])

    if args.delete:
        delete_task(tasks, args.delete[0])

    if args.show:
        try:
            num = int(args.show[0])
        except (ValueError, IndexError):
            num = 5
        show_tasks(tasks, num)

    if args.show_id:
        tid = args.show_id[0]
        if tid in tasks:
            t = tasks[tid]
            print(f"{t['title']}\nPriority: {t['priority']}, Status: {t['status']}")
            print(f"{t['description']}")
        else:
            print(f"Task ID {tid} not found.")


# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------

def get_task_parameters():
    """Get task input from user."""
    title = input("Title: ")
    while True:
        try:
            priority = int(input("Priority 0-5: "))
            if priority < 0 or priority > 5:
                raise ValueError
            break
        except ValueError:
            print("Please enter a number from 0 to 5.")
    description = input("Description: ")
    return title, priority, description


def _get_next_task_id(tasks):
    """Return a globally unique ID."""
    if tasks:
        return str(max(int(k) for k in tasks.keys()) + 1)
    return "1"


def setup():
    """Create JORA directory and CSV files if missing."""
    os.makedirs("JORA", exist_ok=True)
    for filename in ["OPEN.csv", "IN_PROGRESS.csv", "CLOSED.csv"]:
        path = os.path.join("JORA", filename)
        if not os.path.exists(path):
            with open(path, "w", newline="", encoding="utf-8") as f:
                f.write("Title,Priority,Description,ID\n")


def load_tasks_dict(include_closed=True):
    """Load all tasks into a dictionary keyed by ID."""
    tasks = {}
    statuses = ["OPEN", "IN_PROGRESS"]
    if include_closed:
        statuses.append("CLOSED")

    for status in statuses:
        path = f"JORA/{status}.csv"
        if not os.path.exists(path):
            continue
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header
            for row in reader:
                if len(row) >= 4:
                    tid = row[3]
                    tasks[tid] = {
                        "title": row[0],
                        "priority": int(row[1]),
                        "description": row[2],
                        "status": status
                    }
    return tasks


def save_tasks_dict(tasks):
    """Write all tasks back to their respective CSV files."""
    files = {status: [] for status in ["OPEN", "IN_PROGRESS", "CLOSED"]}
    for tid, t in tasks.items():
        files[t["status"]].append([t["title"], t["priority"], t["description"], tid])

    for status, rows in files.items():
        path = f"JORA/{status}.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Title", "Priority", "Description", "ID"])
            writer.writerows(rows)


def create_task(tasks, title, priority, description, verbose=True):
    """Add a new task."""
    tid = _get_next_task_id(tasks)
    tasks[tid] = {
        "title": title,
        "priority": priority,
        "description": description,
        "status": "OPEN"
    }
    save_tasks_dict(tasks)
    if verbose:
        print(f"Added task {title} with ID #{tid} to OPEN")


def move_task(tasks, task_id):
    """Move a task to the next stage."""
    if task_id not in tasks:
        print("Task not found")
        return

    task = tasks[task_id]
    if task["status"] == "OPEN":
        task["status"] = "IN_PROGRESS"
    elif task["status"] == "IN_PROGRESS":
        task["status"] = "CLOSED"
    elif task["status"] == "CLOSED":
        print("Ticket is closed")
        reopen = input("Re-open task? y/n\n").lower()
        if reopen in ["y", "yes"]:
            task["status"] = "IN_PROGRESS"

    save_tasks_dict(tasks)
    print(f"Task ID {task_id} moved to {task['status']}")


def delete_task(tasks, task_id):
    """Delete a task."""
    if task_id not in tasks:
        print("Task not found")
        return
    del tasks[task_id]
    save_tasks_dict(tasks)
    print(f"Task ID {task_id} deleted")


def show_tasks(tasks, num=5, include_closed=False):
    """Show top N tasks by priority."""
    if not isinstance(num, int):
        try:
            num = int(num)
        except:
            num = 5

    filtered = [t for t in tasks.values() if include_closed or t["status"] in ("OPEN", "IN_PROGRESS")]
    sorted_tasks = sorted(filtered, key=lambda x: x["priority"], reverse=True)

    for t in sorted_tasks[:num]:
        print(f"Title: {t['title']}, Priority: {t['priority']}, Status: {t['status']}")


def get_task_count(tasks):
    """Return number of tasks."""
    return len(tasks)


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

if __name__ == "__main__":
    main()
