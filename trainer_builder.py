
#============================================================================
# Name        : trainer_builder.py
# Author      : Abdurrahman Nurhakim
# Version     : 1.0
# Copyright   : Your copyright notice
# Description : to build .yml for training face recognition 
#============================================================================

import cv2
import numpy as np
from PIL import Image
import os

path = 'dataset'
recognizer = cv2.face.LBPHFaceRecognizer_create()
detector = cv2.CascadeClassifier("opencv-3.3.0/data/haarcascades/haarcascade_frontalface_default.xml")

if not os.path.exists('trainer'):
    os.makedirs('trainer')

def getImagesAndLabels(path):
    imagePaths = [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    faceSamples = []
    ids = []
    for imagePath in imagePaths:
        img_name = os.path.splitext(os.path.basename(imagePath))[0]  # Mendapatkan nama file tanpa ekstensi
        id = int(img_name.split(".")[1])  # Mendapatkan ID dari nama file
        PIL_img = Image.open(imagePath).convert('L')
        img_numpy = np.array(PIL_img, 'uint8')
        faceSamples.append(img_numpy)
        ids.append(id)
    return faceSamples, ids

print("\n [INFO] Training faces. It will take a few seconds. Wait ...")
faces, ids = getImagesAndLabels(path)
recognizer.train(faces, np.array(ids))

recognizer.write('trainer/trainer.yml')
print("\n [INFO] {0} faces trained. Exiting Program".format(len(np.unique(ids))))

