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
                if priority < 0 or priority > 5: raise ValueError
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


def create_task(title, priortity, description, count, status="OPEN"):
    with open(f"JORA/{status}.csv", "r", newline="") as infile:
        reader = csv.reader(infile)
        header = next(reader)
        existing_data = list(reader)
        print("existing data :")
        print(existing_data)
        
        existing_data.append([title, priortity, description, count])
        print("existing data after append")
        print(existing_data)

    #TODO something about writing back to the file with the exisiting data is broken

    with open(f"{status}.csv", "w", newline="") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(header)
        writer.writerows(existing_data)


def setup():
    os.mkdir("JORA")
    with open("JORA/OPEN.csv", "w") as file:
        writer = file.write("Title, Priority, Description, ID")
    with open("JORA/IN_PROGRESS.csv", "w") as file:
        writer = file.write("Title, Priority, Description, ID")
    with open("JORA/CLOSED.csv", "w") as file:
        writer = file.write("Title, Priority, Description, ID")


main()