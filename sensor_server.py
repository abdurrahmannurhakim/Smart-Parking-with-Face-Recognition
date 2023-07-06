#============================================================================
# Name        : sensor_server.py
# Author      : Abdurrahman Nurhakim
# Version     : 1.0
# Copyright   : Your copyright notice
# Description : To monitor parking placed via GPIO and update it into firebase
#============================================================================

import pyrebase 
import RPi.GPIO as GPIO 
import sqlite3 
import time 
import os 
import random 
import socket
import errno

# Fungsi untuk memeriksa koneksi internet
def check_internet_connection():
    try:
        # Mencoba membuat koneksi ke host google.com pada port 80
        socket.create_connection(("www.google.com", 80))
        print("koneksi tersedia \n")
        return True
    except OSError:
        return False

check_internet_connection()

# Konfigurasi Firebase
firebase_config = {
  "apiKey": "YOUR API KEY",
  "authDomain": "YOUT AUTH DOMAIN",
  "databaseURL": "YOUR URL",
  "projectId": "YOUR PROJECT ID",
  "storageBucket": "YOUT STORY BUCKET",
}

# Inisialisasi Firebase
firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()

# Mapping pin GPIO dengan nama node
gpio_node_mapping = {
    27: "A1",
    24: "A2",
    5: "A3",
    6: "A4",
    16: "A5",
    20: "A6",
    21: "B1",
    19: "B2",
    26: "B3",
    12: "B4"
}

# Konfigurasi GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Daftar pin GPIO
gpio_pins = list(gpio_node_mapping.keys())

# Konfigurasi pin GPIO
GPIO.setup(gpio_pins, GPIO.IN)

# Membaca status pin GPIO dan mengirim data ke Firebase
data = {"status": "Empty"}

# Membuat direktori 'database' jika belum ada
try:
	os.makedirs('database')
except OSError as e:
	if e.errno != errno.EEXIST:
		raise

# Menghubungkan ke database SQLite
conn = sqlite3.connect(os.path.join('database', 'database.db'))
c = conn.cursor()

# Mengecek apakah tabel 'parkir' sudah ada
c.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='parkir' ''')
table_exists = c.fetchone()

# Jika tabel sudah ada, hapus semua data
if table_exists:
    c.execute("DELETE FROM parkir")
else:
    # Membuat tabel 'parkir'
    c.execute('''CREATE TABLE parkir (
                    position TEXT PRIMARY KEY,
                    status TEXT
                )''')

for pin in gpio_pins:
    if GPIO.input(pin) == 0:
        node_name = gpio_node_mapping.get(pin)
        if node_name:
            data["status"] = "Full"
            db.child("transaction/position/{0}".format(node_name)).update(data)
            c.execute("INSERT INTO parkir (position, status) VALUES (?, ?)", (node_name, data["status"]))
            print("Data telah berhasil dikirim dan dicatat untuk node {0}.".format(node_name))
            time.sleep(1)
    else:
        node_name = gpio_node_mapping.get(pin)
        if node_name:
            data["status"] = "Empty"
            db.child("transaction/position/{0}".format(node_name)).update(data)
            c.execute("INSERT INTO parkir (position, status) VALUES (?, ?)", (node_name, data["status"]))
            print("Data telah berhasil dikirim dan dicatat untuk node {0}.".format(node_name))
            time.sleep(1)
conn.commit()
conn.close()

# Membersihkan konfigurasi GPIO
GPIO.cleanup()

