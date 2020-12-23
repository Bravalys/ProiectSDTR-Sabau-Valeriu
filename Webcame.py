import cv2,time,pandas
import numpy as np
from datetime import datetime
#from firebase import firebase
import os
import pyrebase
import json
# Incarcarea fisierului config pentru conectarea la firebase
with open('config.json') as f:
    config = json.load(f)
    
# Initializarea camerei 
cap = cv2.VideoCapture(0)
cam_width = 720 
cam_height = 480 
# Verificare daca camera a pornit
if not (cap.isOpened()):
    print("Could not open video device")
# Setarea rezolutiei
cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_height)
prev_frame_time = 0
new_frame_time = 0
count_image = 0
# Crearea unei matrici de 7x7 
mask = np.ones((7,7),np.uint8)
display_screen = np.zeros(( (cam_height*2), (cam_width*2), 3) , np.uint8)
motion_threshold = 10000 
# Lista pentru a vedea daca e un inceput de miscare sau sfarsit de miscare
motion_list = [ None, None ]
# Lista pentru a salva data si ora la care s-a produs detectia de miscare
times = []
# Data frame pentru a salva usor intr-un fisier csv
panda_DataFrame = pandas.DataFrame(columns = ["Start"])

# Numele fisierelor pentru salvarea pe dispozitiv si in firebase/cloud
filename = 'savedImage%d.jpg'
path_on_cloud="images/savedImage%d.jpg"
# Initializarea conectiunii cu firebase
firebase = pyrebase.initialize_app(config)
storage = firebase.storage()
db = firebase.database()

while(True): 
    
    succes1, frame1 = cap.read()
    # Conversia frame-ului 2 la gray
    grayImage_Frame1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)  
    succes2, frame2 = cap.read()
    # Conversia frame-ului 2 la gray
    grayImage_Frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)  
    
    motion = 0
    # Diferenta dintre cele 2 frame-uri
    diffImage = cv2.absdiff(grayImage_Frame1,grayImage_Frame2) 
    
    blurImage = cv2.GaussianBlur(diffImage, (5,5), 0)
    _, thresholdImage = cv2.threshold(blurImage, 20,255,cv2.THRESH_BINARY)
    dilatedImage = cv2.dilate(thresholdImage,mask,iterations=3)
    font = cv2.FONT_HERSHEY_SIMPLEX
    new_frame_time = time.time()
    fps = 1/(new_frame_time-prev_frame_time) 
    prev_frame_time = new_frame_time
    fps = int(fps)
    fps = str(fps)
    cv2.putText(frame1, fps, (590, 30), font, 1, (100, 255, 0), 3, cv2.LINE_AA)
    # Crearea contururilor
    contours, _ = cv2.findContours (dilatedImage, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE) 
    # Pentru fiecare detectie
    for contour in contours:
        # Salveaza locatiile
        (x,y,w,h) = cv2.boundingRect(contour) 
        #print(cv2.contourArea(contour))
        # Crearea chenarelor
        if cv2.contourArea(contour) > motion_threshold:
            motion = 1
            print(cv2.contourArea(contour))
            
            cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 1)
    
    motion_list.append(motion)
    motion_list = motion_list[-2:] 
    print(motion_list)
    # Verificare daca e inceputul sau sfarsitul unei detectii de miscare
    if motion_list[-1] == 1 and motion_list[-2] == 0: 
        times.append(datetime.now())
        data = {'Datetime':str(times[-1])}
        db.child("Detections").push(data)

        cv2.imwrite(filename % count_image, frame1)

        storage.child(path_on_cloud%count_image).put(filename%count_image)
        count_image += 1
        
    # Afisarea fereastra video
    cv2.imshow('Live',frame1)
    # Comanda de a inchide fereastra camerei video
    if cv2.waitKey(1) & 0xFF == ord('q'):
        if motion == 1: 
            times.append(datetime.now()) 
        break
    print(times)
cap.release()
cv2.destroyAllWindows()
for i in range(0, len(times), 2): 
    panda_DataFrame = panda_DataFrame.append({"Start":times[i]}, ignore_index = True) 

# Crearea unui fisier .csv pentru a salva data si ora la care s-a produs fiecare detectie de miscare 
panda_DataFrame.to_csv("Time_of_movements.csv") 
print(len(times))