from threading import Thread
import cv2
import time
import cv2, time, pandas
import numpy as np
from datetime import datetime
from firebase import firebase
import os
import pyrebase
import json
from pyfcm import FCMNotification
import threading
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(4, GPIO.OUT)

# Incarcarea fisierului config pentru conectarea la firebase
with open('config.json') as f:
    config = json.load(f)
with open('apikey.json') as f:
    apikey = json.load(f)
# print(apikey['apiKey'])
# Initializarea camerei 
cam_width = 720
cam_height = 480
# Verificare daca camera a pornit

# Setarea rezolutiei


new_frame_time = 0
# Crearea unei matrici de 7x7 
mask = np.ones((7, 7), np.uint8)
display_screen = np.zeros(((cam_height * 2), (cam_width * 2), 3), np.uint8)
motion_threshold = 10000
# Lista pentru a vedea daca e un inceput de miscare sau sfarsit de miscare
# Lista pentru a salva data si ora la care s-a produs detectia de miscare
times = []
# Data frame pentru a salva usor intr-un fisier csv
panda_DataFrame = pandas.DataFrame(columns=["Start"])

# Numele fisierelor pentru salvarea pe dispozitiv si in firebase/cloud
filename = 'savedImage%d.jpg'
path_on_cloud = "images/savedImage%d.jpg"
# Initializarea conectiunii cu firebase
firebase = pyrebase.initialize_app(config)
storage = firebase.storage()
# all_files = storage.child("images").list_files()
# files = storage.list_files()
# storage.delete("images/")
files = storage.list_files()
for file in files:
    print("Un fisier a fost sters")
    storage.delete(file.name)

db = firebase.database()
db.child("Detections").remove()
push_service = FCMNotification(api_key=apikey['apiKey'])
apptoken = db.child("apptoken").get()

print(apptoken.val())


class MotionDetection:
    def __init__(self, src=0, cam_width=720, cam_height=480, motion_list=[0, 0], count_image=0,
                 panda_DataFrame=pandas.DataFrame(columns=["Start"]), stare="off"):
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_height)
        (self.succes1, self.frame1) = self.cap.read()
        self.sem = threading.Semaphore()
        self.started = False
        self.stop_threads = False
        self.motion_list = motion_list
        self.count_image = count_image
        self.panda_DataFrame = panda_DataFrame
        self.stare = stare

    def start(self):
        if self.started:
            print("already started!!")
            return None
        self.started = True

        # Initializarea semaforului si a thread-urilor
        self.sem = threading.Semaphore()
        self.thread = Thread(target=self.update)
        self.thread2 = Thread(target=self.sendToFirebase)
        self.thread.start()
        self.thread2.start()
        return self

    def update(self):
        prev_frame_time = 0

        motion = 0
        while self.started:
            self.sem.acquire()
            (succes1, frame1) = self.cap.read()
            grayImage_Frame1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
            (succes2, frame2) = self.cap.read()
            grayImage_Frame2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
            motion = 0
            # Diferenta dintre cele 2 frame-uri
            diffImage = cv2.absdiff(grayImage_Frame1, grayImage_Frame2)

            blurImage = cv2.GaussianBlur(diffImage, (5, 5), 0)
            _, thresholdImage = cv2.threshold(blurImage, 20, 255, cv2.THRESH_BINARY)
            dilatedImage = cv2.dilate(thresholdImage, mask, iterations=3)
            font = cv2.FONT_HERSHEY_SIMPLEX
            new_frame_time = time.time()
            fps = 1 / (new_frame_time - prev_frame_time)
            prev_frame_time = new_frame_time
            fps = int(fps)
            fps = str(fps)
            cv2.putText(frame1, fps, (590, 30), font, 1, (100, 255, 0), 3, cv2.LINE_AA)
            # Crearea contururilor
            contours, _ = cv2.findContours(dilatedImage, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            # Pentru fiecare detectie
            for contour in contours:
                # Salveaza locatiile
                (x, y, w, h) = cv2.boundingRect(contour)
                # print(cv2.contourArea(contour))
                # Crearea chenarelor
                if cv2.contourArea(contour) > motion_threshold:
                    motion = 1
                    print(cv2.contourArea(contour))

                    cv2.rectangle(frame1, (x, y), (x + w, y + h), (0, 255, 0), 1)

            self.motion_list.append(motion)
            self.motion_list = self.motion_list[-2:]
            print(self.motion_list)
            print("Thread1")
            self.grabbed1, self.frame1 = succes1, frame1
            self.sem.release()
            time.sleep(0.01)

    def read(self):
        frame = self.frame1.copy()
        return frame

    def stop(self):
        self.started = False
        self.thread2.join()
        self.thread.join()
        GPIO.output(4, GPIO.LOW)
        self.cap.release()
        for i in range(0, len(times), 2):
            self.panda_DataFrame = self.panda_DataFrame.append({"Start": times[i]}, ignore_index=True)

            # Crearea unui fisier .csv pentru a salva data si ora la care s-a produs fiecare detectie de miscare
        self.panda_DataFrame.to_csv("Time_of_movements.csv")
        print(len(times))

    def sendToFirebase(self):

        while self.started:
            self.sem.acquire()
            if self.motion_list[-1] == 1 and self.motion_list[-2] == 0:
                self.turnLed("on")
                times.append(datetime.now())
                # data = {'Datetime':str(times[-1])}
                # db.child("Detections").push(data)

                cv2.imwrite(filename % self.count_image, self.frame1)

                storage.child(path_on_cloud % self.count_image).put(filename % self.count_image)
                imagine_url = storage.child(path_on_cloud % self.count_image).get_url(None)
                # Tokenul de aplicatiei pentru dispozitivul android si trimiterea notificarii
                print(imagine_url)
                images = {'imageUrl': str(imagine_url)}
                db.child("Detections").push(images)
                registration_id = apptoken.val()
                message_title = "Atentie!"
                message_body = "A fost detectata o miscare."

                extra_notification_kwargs = {
                    'image': imagine_url
                }
                result = push_service.notify_single_device(registration_id=registration_id, message_title=message_title,
                                                           message_body=message_body,
                                                           extra_notification_kwargs=extra_notification_kwargs)

                self.count_image += 1
            if self.motion_list[-1] == 0 and self.motion_list[-2] == 1:
                self.turnLed("off")
            print("Thread2")
            self.sem.release()
            time.sleep(0.01)

    def turnLed(self, stare):
        self.stare = stare
        if (self.stare == "on"):
            GPIO.output(4, GPIO.HIGH)
            print("LED ON")
        elif (self.stare == "off"):
            GPIO.output(4, GPIO.LOW)
            print("LED ON")


if __name__ == "__main__":
    motionDet = MotionDetection().start()

    while True:
        frame = motionDet.read()
        cv2.imshow('webcam', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            motionDet.stop()
            break

    cv2.destroyAllWindows()
