import cv2
import dlib
from blink import detectBlink
from mouth import detectMouth
from head_pose import detectHeadPose
from eye_gaze import eyeGaze
import json
import datetime

import os
HEADLESS = os.environ.get("HEADLESS", "0") == "1"


face_detector = dlib.get_frontal_face_detector()
cap = cv2.VideoCapture(0)

# # log file
# log_file = "cheating_log.json"

import os
log_file = os.path.join(os.path.dirname(__file__), "cheating_log.json")


def log_event(event_type, value):
    log_entry = {
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event_type,
        "value": value
    }
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector(gray)

    blink = detectBlink(faces, frame)
    mouth = detectMouth(faces, frame)
    head = detectHeadPose(faces, frame)
    gaze = eyeGaze(faces, frame)

    # log suspicious behaviors
    if blink:
        log_event("blink", True)
    if mouth == "Mouth Open":
        log_event("mouth", "open")
    if head in ["Head Left", "Head Right", "Head Up", "Head Down"]:
        log_event("head", head)
    if gaze in ["Looking Left", "Looking Right"]:
        log_event("gaze", gaze)

    # print json for node.js
    status = {"blink": blink, "mouth": mouth, "head": head, "gaze": gaze}
    print(json.dumps(status), flush=True)

    # cv2.imshow("Exam Proctoring System", frame)
    
    if not HEADLESS:
        cv2.imshow("Exam Proctoring", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
