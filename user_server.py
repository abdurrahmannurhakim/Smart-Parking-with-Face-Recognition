#============================================================================
# Name        : user_server.py
# Author      : Abdurrahman Nurhakim
# Version     : 1.0
# Copyright   : Your copyright notice
# Description : for updating local database and retrive data from firebase
#============================================================================

import socket
import requests
import sqlite3
import os
import sys


def check_internet_connection():
    try:
        # Attempt to create a connection to google.com on port 80
        socket.create_connection(("www.google.com", 80))
        return True
    except socket.error:
        return False

# Check internet connection
if not check_internet_connection():
    print("Not connected to the internet. Exiting the program.")
    sys.exit(1)

# Function to create a table
def create_table():
    conn = sqlite3.connect(os.path.join('database', 'database.db'))
    c = conn.cursor()

    # Check if the 'data' table exists in the database
    c.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='data' ''')
    table_exists = c.fetchone()

    # If the table already exists
    if table_exists:
        # Read the last saved data
        c.execute("SELECT status, entry_time, exit_time FROM data ORDER BY unit")
        data_rows = c.fetchall()

        # Save status data to the 'status' array
        for row in data_rows:
            status.append(row[0])
            entry_time.append(row[1])
            exit_time.append(row[2])

    # Drop the table if it already exists to reset the data for new entries from Firebase
    c.execute("DROP TABLE IF EXISTS data")
    # Create the 'data' table
    c.execute('''CREATE TABLE data (
                    id INTEGER PRIMARY KEY,
                    unit TEXT,
                    name TEXT,
                    img TEXT,
                    email TEXT,
                    phone TEXT,
                    license TEXT,
                    status TEXT, 
                    entry_time TEXT,
                    exit_time TEXT
                )''')
    conn.commit()
    conn.close()

# Function to insert data into the table
def insert_data(data):
    conn = sqlite3.connect(os.path.join('database', 'database.db'))
    c = conn.cursor()

    # Insert new data into the table
    sorted_data = sorted(data.items(), key=lambda x: x[1].get('created_at', ''), reverse=False)
    for i, (key, value) in enumerate(sorted_data, start=1):
        unit = value.get('unitNo', '')
        name = value.get('name', '')
        img = value.get('imageUrl', '')
        email = value.get('email', '')
        phone = value.get('phoneNumber', '')
        license = value.get('licenseNumber', '')

        if len(status) > 0:
            status_buff = status[i - 1]
        else:
            status_buff = ''

        if len(entry_time) > 0:
            entry_time_buff = entry_time[i - 1]
        else:
            entry_time_buff = ''

        if len(exit_time) > 0:
            exit_time_buff = exit_time[i - 1]
        else:
            exit_time_buff = ''

        if status_buff == '':
            status_buff = 'OUT'
        if entry_time_buff == '':
            entry_time_buff = 'EMPTY'
        if exit_time_buff == '':
            exit_time_buff = 'EMPTY'

        c.execute("INSERT INTO data (id, unit, name, img, email, phone, license, status, entry_time, exit_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                  (len(sorted_data) - i + 1, unit, name, img, email, phone, license, status_buff, entry_time_buff, exit_time_buff))

    # Update status after all data is inserted
    c.execute("SELECT status, entry_time, exit_time FROM data ORDER BY unit")
    new_statuses = c.fetchall()
    status[:] = []
    entry_time[:] = []
    exit_time[:] = []
    for row in new_statuses:
        status.append(row[0])
        entry_time.append(row[1])
        exit_time.append(row[2])

    conn.commit()
    conn.close()

# Function to read data from the JSON URL
def read_data(url):
    response = requests.get(url)
    data = response.json()
    return data

# JSON URL
url = "YOUR FIRE BASE URL"

# Check internet connection
if not check_internet_connection():
    print "Not connected to the internet. Exiting the program."
    sys.exit(1)

status = []
entry_time = []
exit_time = []

# Read data from the URL
data = read_data(url)

# Create the 'database' directory if it doesn't exist
if not os.path.exists('database'):
    os.makedirs('database')

# Create the table
create_table()

# Insert data into the table
insert_data(data)

print "Operation completed."

