import csv
import sys
import argparse
import os

count = 0

def main():
    if not os.path.exists("JORA"):
        print("creating jora for current project")
        setup()
    
    # Get the parameters from the user calling the python script
    # Create tasks and store them to csv in the appropriate status csv file
    # Move tasks between status states OPEN, IN_PROGRESS, and CLOSED
    # Delete tasks if the user would like


def create_task(title, priortity, description, status="OPEN"):
    with open(f"{status}.csv", 'r+', newline="") as csvfile:
        writer = csv.writer(csvfile, delimeter=" ")
        writer.writerow(title, priortity, description, f"")

def setup():
    os.mkdir("JORA")
    with open("JORA/OPEN.csv", "w") as file:
        writer = file.write("Title, Priority, Description, ID")
    with open("JORA/IN_PROGRESS.csv", "w") as file:
        writer = file.write("Title, Priority, Description, ID")
    with open("JORA/CLOSED.csv", "w") as file:
        writer = file.write("Title, Priority, Description, ID")


main()