
#============================================================================
# Name        : face_recognition_desktop.py
# Author      : Abdurrahman Nurhakim
# Version     : 1.0
# Copyright   : Your copyright notice
# Description : To detect face and recognite it. If the face are recognized, then the portal are open
# Description2: If the portal are open, then the time's history will be saved in local (sqlite) database and firebase
#============================================================================

import socket
import cv2
import numpy as np
import os
import sqlite3
import time
import RPi.GPIO as GPIO
import pyrebase
from datetime import datetime


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

ids = []
names = []
img_urls = []
licenses = []
status = []

def read_database():
        # Load data from SQLite3 database
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, img, license, status FROM data ORDER BY id")
        data = cursor.fetchall()
        conn.close()

        # Convert data into lists
        for row in data:
            ids.append(row[0])
            names.append(row[1])
            img_urls.append(row[2])
            licenses.append(row[3])
            status.append(row[4])
            #print(status)

#face recognition
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')
cascadePath = "opencv-3.3.0/data/haarcascades/haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascadePath)
font = cv2.FONT_HERSHEY_SIMPLEX

#baca kamera usb
cam = cv2.VideoCapture(0)
image = cv2.imread("dummy_picture.png")
#membuat data palsu supaya tidak baca dua kali
ret_buff=None

cam.set(3, 600)
cam.set(4, 600)

minW = 0.1 * cam.get(3)
minH = 0.1 * cam.get(4)

counter_dict = {}
start_time = None
is_program_running = True

servoA_pin = 17  # Ubah pin sesuai dengan pin yang digunakan untuk servoA
servoB_pin = 18  # Ubah pin sesuai dengan pin yang digunakan untuk servoB
sensorA_pin = 22 # pin untuk sensorA
sensorB_pin = 23 # pin untuk sensorB

GPIO.setmode(GPIO.BCM)
#mengatur GPIO sebagai input
GPIO.setup(servoA_pin, GPIO.OUT)
GPIO.setup(servoB_pin, GPIO.OUT)

# Mengatur pin sebagai input
GPIO.setup(sensorA_pin, GPIO.IN)
GPIO.setup(sensorB_pin, GPIO.IN)

# Variabel untuk menyimpan status pembacaan sensor
is_reading_enabled_A = True
sensor_status_A = False

# Variabel untuk menyimpan status pembacaan sensor
is_reading_enabled_B = True
sensor_status_B = False

servoA = GPIO.PWM(servoA_pin, 50)  # PWM dengan frekuensi 50Hz untuk servoA
servoB = GPIO.PWM(servoB_pin, 50)  # PWM dengan frekuensi 50Hz untuk servoB

servoA.start(0)  # Mulai dengan siklus kerja 0 (sudut 0 derajat)
servoB.start(0)  # Mulai dengan siklus kerja 0 (sudut 0 derajat)


def create_database():
    conn = sqlite3.connect(os.path.join('database', 'database.db'))
    c = conn.cursor()
    
    # Memeriksa tabel pada database dengan nama "history"
    c.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='history' ''')
    table_history_exists = c.fetchone()
    
    if not table_history_exists:
        c.execute('''CREATE TABLE history (
                    number INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    license TEXT,
                    status TEXT,
                    time TEXT
                )''')    
    
    conn.commit()
    conn.close()
    
def move_servo(servo, angle):
    duty_cycle = (angle / 18) + 2.5
    servo.ChangeDutyCycle(duty_cycle)
    time.sleep(1)
    servo.ChangeDutyCycle(0)

#Tukar hasil keluaran sensor, karena ketika sensor terbaca harusnya high bukan low
def read_GPIO(input):
    hasil = 0
    if input == 0:
        return 1
    else:
        return 0
    
# Membuat database history jika belum ada
create_database()
print("cek masuk loop")

try:
    while True:
        #BACA SENSOR
        valueA = read_GPIO(GPIO.input(sensorA_pin))
        valueB = read_GPIO(GPIO.input(sensorB_pin))
        #print(valueA)

        if is_reading_enabled_A:
            if valueA == GPIO.HIGH and sensor_status_A:
                print("Sensor A terbaca")
                is_reading_enabled_A = False
                time.sleep(0.2)
                sensor_status_A = False
            else:
                sensor_status_A = True

        if is_reading_enabled_B:
            if valueB == GPIO.HIGH and sensor_status_B:
                print("Sensor B terbaca")
                is_reading_enabled_B = False
                time.sleep(0.2)
                sensor_status_B = False
            else:
                sensor_status_B = True

	#ret, img = cam.read()
	if (is_reading_enabled_A == False or is_reading_enabled_B == False):
	        ret, img = cam.read()
	else:
		ret = ret_buff
		img = image

	height, width, _ = img.shape
	#jika lebar camera melebihi 400x400 maka dilakukan resize ulang, sehingga resolusi sesuai
	if (width > 400 or height > 400):
		scale_percent = min(400.0/ width, 400.0 / height)
		img = cv2.resize(img, None, fx=scale_percent, fy=scale_percent)

        img = cv2.flip(img, 1)
	gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.2,
            minNeighbors=5,
            minSize=(int(minW), int(minH)),
        )

        for (x, y, w, h) in faces:
            read_database()
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            id, confidence = recognizer.predict(gray[y:y + h, x:x + w])
            confidence_value = int(confidence)
            confidence_buffer = "  {0}%".format(round(100 - confidence_value))

            if confidence_value < 100:
                if id in ids:
                    id = names[ids.index(id)]
                else:
                    id = "unknown"
                if confidence_value <90:
                    if start_time is None:
                        start_time = time.time()
                    if id in counter_dict:
                        counter_dict[id] += 1
                    else:
                        counter_dict[id] = 1
            else:
                id = "unknown"
                confidence_buffer = "  {0}%".format(round(100 - confidence_value))

            cv2.putText(
                img,
                str(id),
                (x + 5, y - 5),
                font,
                1,
                (255, 255, 255),
                2
            )
            cv2.putText(
                img,
                str(confidence_buffer),
                (x + 5, y + h - 5),
                font,
                1,
                (255, 255, 0),
                1
            )


        if is_reading_enabled_A == False or is_reading_enabled_B == False:
            cv2.imshow('camera', img)
        
        k = cv2.waitKey(10) & 0xff
        if k == 27:
            is_program_running = False
            break

        if start_time is not None and time.time() - start_time >= 7 and (is_reading_enabled_A == False or is_reading_enabled_B == False):
            read_database()
            person = max(counter_dict, key=counter_dict.get)
            print("\nNama yang terdeteksi:", person)
            print("ID:", ids[names.index(person)])
            print("License: ", licenses[names.index(person)])

            conn = sqlite3.connect(os.path.join('database', 'database.db'))
            c = conn.cursor()

            if len(status) > 0 and (is_reading_enabled_A == False or is_reading_enabled_B == False):
                if status[ids[names.index(person)] - 1] == 'OUT':
                    status_buff = 'IN'
                    buff_id = ids[names.index(person)]
                    time_now_temp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Menyimpan waktu saat ini dengan format "YYYY-MM-DD HH:mm:ss"
                    print("Waktu Masuk = ", time_now_temp)
                    c.execute("UPDATE data SET status = ? WHERE id = ?", (status_buff, buff_id))
                    c.execute("UPDATE data SET entry_time = ? WHERE id = ?", (time_now_temp, buff_id))
                    c.execute("UPDATE data SET exit_time = ? WHERE id = ?", ('EMPTY', buff_id))
                    print("BUKA PALANG MASUK !!")

                    # Data masukan
                    data = {
                        "name": person,
                        "license": licenses[names.index(person)],
                        "status": "user was enter",
                        "entry time": time_now_temp
                    }

                    #update dulu ke local database
                    c.execute("INSERT INTO history (name, license, status, time) VALUES (?, ?, ?, ?)", (person, licenses[names.index(person)], "user was enter", time_now_temp))
                    
                    # Mengirim data ke Firebase Realtime Database
                    db.child("history/" + time_now_temp).set(data)
                    
                    move_servo(servoA, 90)  # Menggerakkan servoA ke sudut 90 derajat
                    time.sleep(10)
                    move_servo(servoA, 0)  # Menggerakkan servoB ke sudut awal
                    conn.commit()
                    is_reading_enabled_A = True
                    is_reading_enabled_B = True
                    cv2.destroyAllWindows()
                    print("done")
                    
                if status[ids[names.index(person)] - 1] == 'IN':
                    status_buff = 'OUT'
                    buff_id = ids[names.index(person)]
                    time_now_temp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Menyimpan waktu saat ini dengan format "YYYY-MM-DD HH:mm:ss"
                    c.execute("UPDATE data SET status = ? WHERE id = ?", (status_buff, buff_id))
                    c.execute("UPDATE data SET exit_time = ? WHERE id = ?", (time_now_temp, buff_id))
                    print("Waktu keluar = ", time_now_temp)
                    print("BUKA PALANG KELUAR !!")

                    # Data masukan
                    data = {
                        "name": person,
                        "license": licenses[names.index(person)],
                        "status": "user was exit",
                        "exit time": time_now_temp
                    }
                    
                    #update dulu ke local database
                    c.execute("INSERT INTO history (name, license, status, time) VALUES (?, ?, ?, ?)", (person, licenses[names.index(person)], "user was exit", time_now_temp))

                    # Mengirim data ke Firebase Realtime Database
                    db.child("history/" + time_now_temp).set(data)
                    
                    move_servo(servoB, 90)  # Menggerakkan servoB ke sudut 90 derajat
                    time.sleep(10)
                    move_servo(servoB, 0)  # Menggerakkan servoB ke sudut awal
                    conn.commit()
                    is_reading_enabled_A = True
                    is_reading_enabled_B = True
                    cv2.destroyAllWindows()
                    print("done")
                conn.close()
                ids = []
                names = []
                img_urls = []
                licenses = []
                status = []    
            ids = []
            names = []
            img_urls = []
            licenses = []
            status = []
            start_time = None
            #break
        ids = []
        names = []
        img_urls = []
        licenses = []
        status = []        
except KeyboardInterrupt:
    pass
    servoA.stop()
    servoB.stop()
    GPIO.cleanup()
    print("\n[INFO] Exiting Program and cleanup stuff")
    cam.release()
    cv2.destroyAllWindows()

servoA.stop()
servoB.stop()
GPIO.cleanup()

print("\n[INFO] Exiting Program and cleanup stuff")
cam.release()
cv2.destroyAllWindows()
