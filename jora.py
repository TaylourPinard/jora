import csv
import sys
import argparse
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--new", action="store_true", help="create a new ticket")
    parser.add_argument("-mv", "--move", nargs=3, help="move a ticket. usage '-mv <id> <source_file> <destination_file>'")
    parser.add_argument("-x", "--delete", nargs=1, help="delete a ticket")
    parser.add_argument("-s", "--show", nargs=1, help="number of tickets to show")

    args = parser.parse_args()

    if not os.path.exists("JORA"):
        setup()

    if len(sys.argv) == 1:
        show_tasks()

    if args.new:
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
        create_task(title, priority, description)

    if args.move:
        move_task(args.move[0], args.move[1], args.move[2])

    if args.delete:
        delete_task(args.delete[0])

    if args.show:
        show_tasks(sys.argv[2])


def _get_next_task_id():
    """Return a globally unique ID across all CSV files."""
    ids = set()
    for filename in ["OPEN.csv", "IN_PROGRESS.csv", "CLOSED.csv"]:
        path = os.path.join("JORA", filename)
        if not os.path.exists(path):
            continue
        with open(path, "r", newline="") as file:
            reader = csv.reader(file)
            next(reader, None)  # skip header
            for row in reader:
                if len(row) >= 4:
                    try:
                        ids.add(int(row[3]))
                    except ValueError:
                        pass
    return max(ids) + 1 if ids else 1


def create_task(title, priority, description, task_id=None, status="OPEN"):
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

    with open(file_path, "a", newline="") as outfile:
        writer = csv.writer(outfile)
        writer.writerow([title, priority, description, task_id])

    print(f"Added new task #{task_id} to {status}")


# I feel like this can be refactored to take into account the current location of the task
# and move it to the next logical destination OPEN -> IN_PROGRESS -> CLOSED

def move_task(task_id, source, destination):
    """Move a task (preserving its ID) from one CSV file to another."""
    data = []
    ticket = None

    src_path = f"JORA/{source}.csv"
    dest_path = f"JORA/{destination}.csv"

    if not os.path.exists(src_path):
        print(f"Source file {source}.csv not found.")
        return

    with open(src_path, "r", newline="") as file:
        reader = csv.reader(file)
        header = next(reader)
        for entry in reader:
            if len(entry) < 4:
                continue
            if entry[3] != str(task_id):
                data.append(entry)
            else:
                ticket = entry

    if ticket is None:
        print(f"Ticket {task_id} not found in {source}.csv")
        return

    create_task(ticket[0], ticket[1], ticket[2], status=destination, task_id=ticket[3])

    with open(src_path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(data)


def delete_task(task_id):
    data = []
    for filename in ["OPEN.csv", "IN_PROGRESS.csv", "CLOSED.csv"]:
        with open(f"JORA/{filename}", "r", newline="") as file:
            reader = csv.reader(file)
            data.append(next(reader))
            for entry in reader:
                if entry[3] != task_id:
                    data.append(entry)
        with open(f"JORA/{filename}", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerows(data)


def setup():
    """Create JORA directory and CSV structure if not present."""
    os.makedirs("JORA", exist_ok=True)
    for filename in ["OPEN.csv", "IN_PROGRESS.csv", "CLOSED.csv"]:
        path = os.path.join("JORA", filename)
        if not os.path.exists(path):
            with open(path, "w", newline="") as file:
                file.write("Title,Priority,Description,ID\n")


def get_task_count():
    """Return total number of tasks across all CSV files."""
    count = 0
    for n in ["OPEN", "IN_PROGRESS", "CLOSED"]:
        path = f"JORA/{n}.csv"
        if not os.path.exists(path):
            continue
        with open(path, "r", newline="") as file:
            reader = csv.reader(file)
            next(reader, None)
            count += sum(1 for _ in reader)
    return count


def show_tasks(num=5):
    data = []
    with open("JORA/IN_PROGRESS.csv", "r", newline="") as file:
        reader = csv.reader(file)
        next(reader)
        for entry in reader:
            entry.append("IN_PROGRESS")
            data.append(entry)
    if len(data) < 5:
        with open("JORA/OPEN.csv", "r", newline="") as file:
            reader = csv.reader(file)
            next(reader)
            for entry in reader:
                entry.append("OPEN")
                data.append(entry)
    sorted_data = sorted(data, key=lambda x: int(x[1]), reverse=True)
    for i in range(min(int(num), len(sorted_data))):
        print(f"Title: {sorted_data[i][0]}, Priority: {sorted_data[i][1]}, Status: {sorted_data[i][4]}")

if __name__ == "__main__":
    main()
