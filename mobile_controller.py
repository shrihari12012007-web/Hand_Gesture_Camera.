import cv2
import os
import sys
import time
import platform
import pyautogui

try:
    from hand_gesture import HandGesture
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from hand_gesture import HandGesture

# Configure PyAutoGUI responsiveness
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

print("Starting Mobile Gesture Controller Simulator (Single-Fire Mode)...")

def open_working_camera():
    backends = [cv2.CAP_DSHOW, cv2.CAP_ANY] if platform.system() == "Windows" else [cv2.CAP_ANY]
    for idx in [0, 1, 2]:
        for backend in backends:
            cap = cv2.VideoCapture(idx, backend)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    return cap
                cap.release()
    return None

cap = open_working_camera()

if cap is None:
    print("ERROR: Could not open any webcam. Please ensure camera is connected and not in use by another app.")
    sys.exit(1)

# Single-hand detector
try:
    hand_detector = HandGesture(max_num_hands=1, min_detection_confidence=0.4, min_tracking_confidence=0.4)
except Exception as e:
    print(f"ERROR: Failed to initialize HandGesture: {e}")
    cap.release()
    sys.exit(1)

# State lock variables
previous_gesture = "NONE"
gesture = "READY - SHOW HAND"

try:
    while True:
        success, frame = cap.read()
        if not success or frame is None:
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
                    gesture = "PALM -> NEXT TRACK"
                    pyautogui.press("nexttrack")
                    print("ACTION: Next Track")

                elif current_detected == "FIST":
                    gesture = "FIST -> MUTE / UNMUTE"
                    pyautogui.press("volumemute")
                    print("ACTION: Mute / Unmute")

                previous_gesture = current_detected
        else:
            previous_gesture = "NONE"
            gesture = "NO HAND DETECTED"

        # On-Screen Feedback
        cv2.putText(frame, f"State: {gesture}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
        cv2.putText(frame, "Single-Hand Controller | Press Q to Exit", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow("Mobile Controller Simulator", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()
    print("Camera closed.")
