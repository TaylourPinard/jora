import csv
import sys
import argparse
import os


def main():
    count = 0
    
    if not os.path.exists("JORA"):
        print("creating jora for current project")
        setup()
    
    else:
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
        count += 1

        create_task(title, priority, description, count)

    # Get the parameters from the user calling the python script
    # Create tasks and store them to csv in the appropriate status csv file
    # Move tasks between status states OPEN, IN_PROGRESS, and CLOSED
    # Delete tasks if the user would like


def create_task(title, priority, description, count, status="OPEN"):
    file_path = f"JORA/{status}.csv"

    with open(file_path, "r", newline="") as infile:
        reader = csv.reader(infile)
        existing_data = list(reader)
        count = len(existing_data)

    with open(file_path, "a", newline="") as outfile:
        writer = csv.writer(outfile)
        writer.writerow([title, priority, description, count])

    print(f"Added new task #{count} to {status}")

def setup():
    os.mkdir("JORA")
    with open("JORA/OPEN.csv", "w") as file:
        csv.writer = file.write("Title,Priority,Description,ID\n")
    with open("JORA/IN_PROGRESS.csv", "w") as file:
        csv.writer = file.write("Title,Priority,Description,ID\n")
    with open("JORA/CLOSED.csv", "w") as file:
        csv.writer = file.write("Title,Priority,Description,ID\n")


main()