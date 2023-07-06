#============================================================================
# Name        : capture_img_from_database.py
# Author      : Abdurrahman Nurhakim
# Version     : 1.0
# Copyright   : Your copyright notice
# Description : retrive data from firebase then update it into local database 
# Description2 : Take a picture and save it for dataset from url inside the firebase form
#============================================================================

import cv2
import urllib2
import numpy as np
import sqlite3
import requests

# Fungsi untuk mendeteksi wajah dalam gambar
def detect_faces(image_url, face_id, name, license):
    # Muat Cascade Classifier untuk deteksi wajah
    cascade_path = "opencv-3.3.0/data/haarcascades/haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)

    try:
        # Baca gambar dari URL
        resp = urllib2.urlopen(image_url)
        image = np.asarray(bytearray(resp.read()), dtype=np.uint8)
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)

        # Periksa resolusi gambar
        height, width, _ = image.shape
        if width > 400 or height > 400:
            scale_percent = max(400.0 / width, 400.0 / height)
            new_width = int(width * scale_percent)
            new_height = int(height * scale_percent)
            image = cv2.resize(image, (new_width, new_height))

        # Ubah gambar menjadi grayscale untuk deteksi wajah
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Deteksi wajah dalam gambar
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

        # Gambar kotak di sekitar wajah yang terdeteksi
        for (x, y, w, h) in faces:
            # Tampilkan kotak dengan koordinat asli tanpa konversi
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Simpan gambar yang berisi wajah yang terdeteksi
            cv2.imwrite("dataset/" + name + '.' + str(face_id) + '.' + license + ".jpg", gray[y:y+h, x:x+w])

        # Tampilkan gambar dengan wajah yang terdeteksi
        cv2.imshow('Detected Faces', image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    except IOError as e:
        print "Error:", e

    except Exception as e:
        print "Request failed:", str(e)


# Koneksi ke database
conn = sqlite3.connect('database/database.db')
cursor = conn.cursor()

# Query untuk mendapatkan data dari tabel
query = "SELECT id, name, img, license FROM data ORDER BY id"

# Eksekusi query
cursor.execute(query)

# Fetch semua baris hasil query
rows = cursor.fetchall()

# Loop melalui setiap baris
for row in rows:
    face_id = row[0]
    name = row[1]
    img_url = row[2]
    license = row[3]

    try:
        # Panggil fungsi deteksi wajah dengan URL gambar
        detect_faces(img_url, face_id, name, license)

    except requests.exceptions.RequestException as e:
        print "Request failed:", str(e)

# Tutup koneksi ke database
conn.close()

