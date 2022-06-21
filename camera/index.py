import cv2
import dlib
import time
import threading
import math
import os
import requests
from flask import Flask, Response
import threading
import queue
from parking import registerEntry

carCascade = cv2.CascadeClassifier('haar.xml')
video = cv2.VideoCapture('car_video.mp4')

PATH = os.path.join(os.getcwd(), 'images')
FILE_PATH = os.path.join(os.getcwd(), 'list.txt')
WIDTH = 1920
HEIGHT = 1080
MIN_WIDTH = 100
MIN_HEIGHT = 100
API_KEY = "02f97a914ac21efe0f718cc3acbd0ebce3d1dc5e"
SPEED_LIMIT = 0
MAX_NUM_THREADS = 4


lock = threading.Lock()
vehicles = queue.Queue(maxsize=50)

app = Flask(__name__)
resultImage = []


def getRegistrationNumber():
    print('Entering registration number thread')
    while True:
        if(vehicles.empty()):
            time.sleep(2)
            continue

        car_id = vehicles.get()
        image_path = os.path.join(PATH, f'car{car_id}.jpg')
        with open(image_path, 'rb') as fp:
            response = requests.post(
                'https://api.platerecognizer.com/v1/plate-reader/',
                # Optional
                files=dict(upload=fp),
                headers={'Authorization': f'Token {API_KEY}'},
            )

        result = response.json()

        print(f'Car {car_id}:', end=' ')
        try:
            # print(result['results'][0]['plate'])
            registerEntry(result['results'][0]['plate'])
        except:
            print('No registration number detected')

        time.sleep(1)


# def overspeeding():

#     while True:

#         print('Started running overspeeding')
#         if(vehicles.empty()):
#             print('Running Thread Overspeeding')
#             time.sleep(5)
#             continue

#         car_id = vehicles.get()
#         print(f'Popped Car: {car_id}')

#         with open(os.path.join(PATH, f'car{car_id}.jpg'), 'rb') as fp:
#             response = requests.post(
#                 'https://api.platerecognizer.com/v1/plate-reader/',
#                 # Optional
#                 files=dict(upload=fp),
#                 headers={'Authorization': f'Token {API_KEY}'},
#             )

#         result = response.json()

#         if(not len(result['results'])):
#             print("plate not recognised")
#             break
#         else:
#             print(result['results'][0]['plate'])
#             print(result['results'][0]['vehicle'])


# def estimateSpeed(location1, location2):
#     d_pixels = math.sqrt(
#         math.pow(location2[0] - location1[0], 2) +
#         math.pow(location2[1] - location1[1], 2)
#     )
#     # ppm = location2[2] / carWidht
#     ppm = 8.8
#     d_meters = d_pixels / ppm
#     # print("d_pixels=" + str(d_pixels), "d_meters=" + str(d_meters))
#     fps = 18
#     speed = d_meters * fps * 3.6
#     return speed


def detectCars():

    global resultImage

    rectangleColor = (0, 255, 0)
    frameCounter = 0
    currentCarID = 0
    fps = 0

    carTracker = {}
    carNumbers = {}
    carLocation1 = {}
    carLocation2 = {}
    speed = [None] * 1000

    # Write output to video file
    # out = cv2.VideoWriter('outpy.avi',cv2.VideoWriter_fourcc('M','J','P','G'), 10, (WIDTH,HEIGHT))

    while True:
        # file = open(FILE_PATH, "w+")
        start_time = time.time()
        _, image = video.read()
        if type(image) == type(None):
            break

        image = cv2.resize(image, (WIDTH, HEIGHT))
        resultImage = image.copy()

        frameCounter += 1

        carIDtoDelete = []

        for carID in carTracker.keys():
            trackingQuality = carTracker[carID].update(image)

            if trackingQuality < 15:
                carIDtoDelete.append(carID)

        for carID in carIDtoDelete:
            carTracker.pop(carID, None)
            carLocation1.pop(carID, None)
            carLocation2.pop(carID, None)

        if not (frameCounter % 10):
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            cars = carCascade.detectMultiScale(gray, 1.1, 13, 18, (24, 24))

            for (_x, _y, _w, _h) in cars:
                x = int(_x)
                y = int(_y)
                w = int(_w)
                h = int(_h)

                x_bar = x + 0.5 * w
                y_bar = y + 0.5 * h

                matchCarID = None

                for carID in carTracker.keys():
                    trackedPosition = carTracker[carID].get_position()

                    t_x = int(trackedPosition.left())
                    t_y = int(trackedPosition.top())
                    t_w = int(trackedPosition.width())
                    t_h = int(trackedPosition.height())

                    t_x_bar = t_x + 0.5 * t_w
                    t_y_bar = t_y + 0.5 * t_h

                    if ((t_x <= x_bar <= (t_x + t_w)) and (t_y <= y_bar <= (t_y + t_h)) and (x <= t_x_bar <= (x + w)) and (y <= t_y_bar <= (y + h))):
                        matchCarID = carID
                        break

                if matchCarID is None and w > MIN_WIDTH and h > MIN_HEIGHT:

                    # print(f'Creating new tracker for {currentCarID}')

                    # cropping the detected vehicle and saving it in images folder
                    crop = image[y:y+h, x:x+w]
                    cv2.imwrite(
                        os.path.join(PATH, f'car{currentCarID}.jpg'),
                        crop
                    )

                    # registration_number = getRegistrationNumber(currentCarID)
                    # print(registration_number)
                    vehicles.put(currentCarID)

                    tracker = dlib.correlation_tracker()
                    tracker.start_track(
                        image, dlib.rectangle(x, y, x + w, y + h))

                    carTracker[currentCarID] = tracker
                    carLocation1[currentCarID] = [x, y, w, h]

                    currentCarID += 1

        # cv2.line(resultImage,(0,480),(1280,480),(255,0,0),5)

        for carID in carTracker.keys():
            trackedPosition = carTracker[carID].get_position()

            t_x = int(trackedPosition.left())
            t_y = int(trackedPosition.top())
            t_w = int(trackedPosition.width())
            t_h = int(trackedPosition.height())

            cv2.rectangle(resultImage, (t_x, t_y),
                          (t_x + t_w, t_y + t_h), rectangleColor, 4)

            # speed estimation
            carLocation2[carID] = [t_x, t_y, t_w, t_h]

        end_time = time.time()

        if not (end_time == start_time):
            fps = 1.0 / (end_time - start_time)

        cv2.putText(resultImage,
                    f'FPS: {int(fps)}',
                    (620, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (0, 0, 255),
                    2
                    )

        # for i in carLocation1.keys():
        #     if frameCounter % 1 == 0:
        #         [x1, y1, w1, h1] = carLocation1[i]
        #         [x2, y2, w2, h2] = carLocation2[i]

        #         # print 'previous location: ' + str(carLocation1[i]) + ', current location: ' + str(carLocation2[i])
        #         carLocation1[i] = [x2, y2, w2, h2]

        #         # print 'new previous location: ' + str(carLocation1[i])
        #         if [x1, y1, w1, h1] != [x2, y2, w2, h2]:
        #             if (speed[i] == None or speed[i] == 0) and y1 >= 275 and y1 <= 285:
        #                 speed[i] = estimateSpeed(
        #                     [x1, y1, w1, h1],
        #                     [x2, y2, w2, h2]
        #                 )
        #                 if int(speed[i]) > SPEED_LIMIT:
        #                     vehicles.put(i)
        #                     print(f'Pushed Overspeeding Vehicle: {i}')
        #                     # overspeeding()
        #             # if y1 > 275 and y1 < 285:
        #             if speed[i] != None and y1 >= 180:
        #                 cv2.putText(resultImage, str(int(speed[i])) + " km/hr", (int(x1 + w1/2), int(
        #                     y1-5)), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

        #             # print ('CarID ' + str(i) + ': speed is ' + str("%.2f" % round(speed[i], 0)) + ' km/h.\n')

        #             # else:
        #             #	cv2.putText(resultImage, "Far Object", (int(x1 + w1/2), int(y1)),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        #                 # print ('CarID ' + str(i) + ' Location1: ' + str(carLocation1[i]) + ' Location2: ' + str(carLocation2[i]) + ' speed is ' + str("%.2f" % round(speed[i], 0)) + ' km/h.\n')
        # cv2.imshow('result', resultImage)

        # Write the frame into the file 'output.avi'
        # out.write(resultImage)

        if cv2.waitKey(33) == 27:
            break

    cv2.destroyAllWindows()


def generate():

    # grab global references to the output frame and lock variables

    # loop over frames from the output stream
    global resultImage, lock

    while True:

        with lock:
            # wait until the lock is acquired

            # check if the output frame is available, otherwise skip
            # the iteration of the loop

            if resultImage is None:
                continue

            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", resultImage)

            # ensure the frame was successfully encoded
            if not flag:
                continue

        # yield the output frame in the byte format
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' +
              bytearray(encodedImage) + b'\r\n')


@ app.route("/overspeed")
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == '__main__':

    t1 = threading.Thread(target=detectCars)
    t1.daemon = True
    t1.start()

    t2 = threading.Thread(target=getRegistrationNumber)
    t2.daemon = True
    t2.start()

    # t2 = threading.Thread(target=overspeeding)
    # t2.daemon = True
    # t2.start()
    # trackMultipleObjects()

    app.run(host='127.0.0.1', port='3001', debug=True,
            threaded=True, use_reloader=False)
