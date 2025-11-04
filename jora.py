#!/usr/bin/env python3
'''
Jora is my implemenetation of a command line jira-style ticket tracking system using python
'''

import csv
import sys
import argparse
import os


#TODO convert this to use a dictionary instead of an array for the data
# the key will be the id

def main():
    '''Main function'''

    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--new", action="store_true", help="create a new task")
    parser.add_argument("-mv", "--move", nargs=1, help="move a task. usage '-mv <id>'")
    parser.add_argument("-x", "--delete", nargs=1, help="delete a task")
    parser.add_argument("-s", "--show", nargs=1, help="number of tasks to show" +
    " usage: '-s (optional <num>)' ")
    parser.add_argument("-id", "--show-id", nargs=1, help="show all task info for " +
        "the id specified. usage '-id <id>'"    
    )

    args = parser.parse_args()

    if not os.path.exists("JORA"):
        setup()

    tasks = get_all_tasks()

    if len(sys.argv) == 1:
        if len(tasks) > 0:
            show_tasks(tasks)
        else:
            title, priority, description = get_task_parameters()
            create_task(title, priority, description)

    if args.new:
        title, priority, description = get_task_parameters()
        create_task(title, priority, description)

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
        for task in tasks:
            if task[3] == args.show_id[0]:
                print(f"{task[0]}\nPriority: {task[1]} status: {task[4]}")
                print(f"{task[2]}")


def get_task_parameters():
    ''' helper function to get the task parameters from a user creating a new task '''
    title = input("Title: ")
    while True:
        try:
            priority = int(input("Priority 0 - 5: "))
            if priority < 0 or priority > 5:
                raise ValueError
            break
        except ValueError:
            print("please only enter a number from 0 to 5")

    description = input("Description: ")
    return title, priority, description

def _get_next_task_id():
    """Return a globally unique ID across all CSV files."""
    ids = set()
    for filename in ["OPEN.csv", "IN_PROGRESS.csv", "CLOSED.csv"]:
        path = os.path.join("JORA", filename)
        if not os.path.exists(path):
            continue
        with open(path, "r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader, None)  # skip header
            for row in reader:
                if len(row) >= 4:
                    try:
                        ids.add(int(row[3]))
                    except ValueError:
                        pass
    return max(ids) + 1 if ids else 1


def create_task(title, priority, description, task_id=None, status="OPEN", verbose=True):
    """
    Create a new task in the specified CSV file.
    - If task_id is None, a new globally unique one is generated.
    - If task_id is provided, it will be preserved (used for moves).
    """
    file_path = f"JORA/{status}.csv"

    # Determine ID
    if task_id is None:
        task_id = _get_next_task_id()
    else:
        try:
            task_id = int(task_id)
        except ValueError:
            task_id = _get_next_task_id()

    with open(file_path, "a", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerow([title, priority, description, task_id])
    if verbose:
        print(f"Added task {title}, with id #{task_id} to {status}")


def move_task(tasks, task_id):
    """Move a task (preserving its ID) from one CSV file to another."""
    task = None
    for x in tasks:
        if x[3] == task_id:
            task = x
    if task is None:
        print("Task not found with that id")
        return
    match task[4]:
        case "OPEN":
            dest = "IN_PROGRESS"
        case "IN_PROGRESS":
            dest = "CLOSED"
        case "CLOSED":
            print("Ticket is closed")
            reopen = input("Re-open task? y/n\n").lower()
            if reopen in ["y", "yes"]:
                dest = "IN_PROGRESS"


    create_task(task[0], task[1], task[2], status=dest, task_id=task[3])
    delete_task(tasks, task_id)


def delete_task(tasks, task_id):
    '''Delete a task by its id number and purge it from the JORA files'''
    status = None
    new = []
    for task in tasks:
        if task[3] == task_id:
            status = task[4]
    if status is None:
        return
    for task in tasks:
        if task[4] == status and task[3]!= task_id:
            new.append(task)
    with open(f"JORA/{status}.csv", "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow("Title,Priority,Description,ID\n")
        writer.writerows(new)


def setup():
    """Create JORA directory and CSV structure if not present."""
    os.makedirs("JORA", exist_ok=True)
    for filename in ["OPEN.csv", "IN_PROGRESS.csv", "CLOSED.csv"]:
        path = os.path.join("JORA", filename)
        if not os.path.exists(path):
            with open(path, "w", newline="", encoding="utf-8") as file:
                file.write("Title,Priority,Description,ID\n")


def get_task_count():
    """Return total number of tasks across all CSV files."""
    count = 0
    for n in ["OPEN", "IN_PROGRESS", "CLOSED"]:
        path = f"JORA/{n}.csv"
        if not os.path.exists(path):
            continue
        with open(path, "r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader, None)
            count += sum(1 for _ in reader)
    return count


def get_all_tasks(include_closed=True):
    '''
    This is a helper function for any time we need to get tasks from files
    so we can sort or print the data as required
    '''
    tasks = []
    status = ["OPEN", "IN_PROGRESS"]
    if include_closed:
        status.append("CLOSED")
    for file_name in status:
        with open(f"JORA/{file_name}.csv", "r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)
            for entry in reader:
                entry.append(f"{file_name}")
                tasks.append(entry)
    return tasks


def show_tasks(tasks, num=5, include_closed=False):
    """
    Show the top <num> priority tasks from OPEN and IN_PROGRESS.
    Tasks are sorted by priority (descending).
    """
    # Normalize num argument (can be int, str, list from argparse)
    if isinstance(num, list):
        if len(num) > 0:
            num = num[0]
        else:
            num = 5

    try:
        num = int(num)
    except (ValueError, TypeError):
        num = 5

    # Filter only OPEN and IN_PROGRESS tasks
    if not include_closed:
        filtered = [t for t in tasks if t[4] in ("OPEN", "IN_PROGRESS")]
        sorted_tasks = sorted(filtered, key=lambda x: x[1], reverse=True)

    # Sort by priority (highest first)
    else:
        sorted_tasks = sorted(tasks, key=lambda x: int(x[1]), reverse=True)

    # Show up to <num> results
    for i in range(min(num, len(sorted_tasks))):
        print(
            f"Title: {sorted_tasks[i][0]}, Priority: {sorted_tasks[i][1]}," +
            f" Status: {sorted_tasks[i][4]}, ID: {sorted_tasks[i][3]}"
        )


if __name__ == "__main__":
    main()
