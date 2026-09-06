import cv2
import os
import sys
import time
import platform
import pyautogui
from hand_gesture import HandGesture

# Configure PyAutoGUI responsiveness
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

print("Starting Mobile Gesture Controller Simulator (Single-Fire Mode)...")

# Initialize camera feed
if platform.system() == "Windows":
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
else:
    cap = cv2.VideoCapture(0)

if not cap.isOpened():
    cap.release()
    cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Camera could not be opened.")
    sys.exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
time.sleep(1)

# Single-hand detector
hand_detector = HandGesture(max_num_hands=1, min_detection_confidence=0.4, min_tracking_confidence=0.4)

# State lock variables
previous_gesture = "NONE"
gesture = "READY - SHOW HAND"

while True:
    success, frame = cap.read()
    if not success:
        time.sleep(0.01)
        continue

    frame = cv2.flip(frame, 1)

    try:
        frame, all_hands = hand_detector.detect_hand(frame)
    except Exception:
        all_hands = []

    current_detected = "NONE"

    if all_hands and len(all_hands) > 0:
        lm = all_hands[0]

        index_tip = lm[8]
        middle_tip = lm[12]
        ring_tip = lm[16]
        pinky_tip = lm[20]

        # Finger PIP joints for extension checks
        index_up = index_tip.y < lm[6].y
        middle_up = middle_tip.y < lm[10].y
        ring_up = ring_tip.y < lm[14].y
        pinky_up = pinky_tip.y < lm[18].y

        # Classification
        is_fist = (not index_up) and (not middle_up) and (not ring_up) and (not pinky_up)
        is_palm = index_up and middle_up and ring_up and pinky_up
        one_finger = index_up and (not middle_up) and (not ring_up) and (not pinky_up)
        two_fingers = index_up and middle_up and (not ring_up) and (not pinky_up)
        three_fingers = index_up and middle_up and ring_up and (not pinky_up)

        if one_finger:
            current_detected = "ONE_FINGER"
        elif two_fingers:
            current_detected = "TWO_FINGERS"
        elif three_fingers:
            current_detected = "THREE_FINGERS"
        elif is_palm:
            current_detected = "PALM"
        elif is_fist:
            current_detected = "FIST"
        else:
            current_detected = "UNKNOWN"

        # Latch logic: Execute only on the rising edge of a new gesture
        if current_detected != previous_gesture:
            if current_detected == "ONE_FINGER":
                gesture = "INDEX FINGER -> TAP / PAUSE"
                pyautogui.press("space")
                print("ACTION: Tap / Pause (Space)")

            elif current_detected == "TWO_FINGERS":
                gesture = "2 FINGERS -> VOLUME UP (+)"
                pyautogui.press("volumeup", presses=2)
                print("ACTION: Volume Up")

            elif current_detected == "THREE_FINGERS":
                gesture = "3 FINGERS -> VOLUME DOWN (-)"
                pyautogui.press("volumedown", presses=2)
                print("ACTION: Volume Down")

            elif current_detected == "PALM":
                gesture = "OPEN PALM -> NEXT"
                pyautogui.press("down")
                print("ACTION: Next (Down Arrow)")

            elif current_detected == "FIST":
                gesture = "CLOSED PALM / FIST -> PREVIOUS"
                pyautogui.press("up")
                print("ACTION: Previous (Up Arrow)")

            previous_gesture = current_detected
        else:
            # Gesture is being held; show status without re-executing
            if current_detected == "PALM":
                gesture = "PALM HELD (1-TIME ACTION COMPLETE)"
            elif current_detected == "FIST":
                gesture = "FIST HELD (1-TIME ACTION COMPLETE)"
            elif current_detected == "ONE_FINGER":
                gesture = "INDEX HELD (1-TIME ACTION COMPLETE)"
            elif current_detected == "TWO_FINGERS":
                gesture = "2 FINGERS HELD (1-TIME ACTION COMPLETE)"
            elif current_detected == "THREE_FINGERS":
                gesture = "3 FINGERS HELD (1-TIME ACTION COMPLETE)"
    else:
        previous_gesture = "NONE"
        gesture = "NO HAND DETECTED"

    # Status Overlay
    cv2.putText(frame, f"Gesture: {gesture}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.70, (0, 255, 0), 2)
    cv2.putText(frame, "1 Finger: Tap/Pause | 2 Fingers: Vol + | 3 Fingers: Vol -", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.putText(frame, "Open Palm: Next | Fist: Prev | Single-Fire Mode Active", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.putText(frame, "Press Q to Exit", (20, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 0, 255), 2)

    cv2.imshow("Mobile Hand Gesture Simulator", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("Controller terminated.")