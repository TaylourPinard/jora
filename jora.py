import csv
import sys
import argparse
import os
    
    #TODO
    # Get the parameters from the user calling the python script
    # Delete tasks if the user would like
    # Implement showing the user contents of their ticket system with configurable flag
    #based command line info

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


def move_task(task_id, source, destination):
    data = []
    
    with open(f"JORA/{source}.csv", "r", newline="") as file:
        reader = csv.reader(file)
        header = next(reader)
        for entry in reader:
            if entry[3] != str(task_id):
                data.append(entry)
            else:
                ticket = entry
   
        try:
            create_task(ticket[0], ticket[1], ticket[2], ticket[3], f"{destination}")
        except:
            print(f"ticket not found in {source}.csv")
            return    

    with open(f"JORA/{source}.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(data)

def setup():
    os.mkdir("JORA")

    for filename in ["OPEN.csv", "IN_PROGRESS.csv", "CLOSED.csv"]:
        with open(f"JORA/{filename}", "w", newline="") as file:
            file.write("Title,Priority,Description,ID\n")


main()