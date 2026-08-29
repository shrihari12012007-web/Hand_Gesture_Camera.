import cv2
import os
import time
import math
import numpy as np
import pyautogui
from datetime import datetime
from hand_gesture import HandGesture


# =====================================================
# SETTINGS
# =====================================================

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

screen_width, screen_height = pyautogui.size()
print("Screen size:", screen_width, "x", screen_height)


# =====================================================
# CAMERA
# =====================================================

print("Starting camera...")

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("DirectShow failed. Trying default camera...")
    cap.release()
    cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Camera could not be opened.")
    exit()

print("Camera opened successfully!")

cam_width, cam_height = 1280, 720
cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_height)

time.sleep(2)


# =====================================================
# HAND DETECTOR
# =====================================================

hand_detector = HandGesture()


# =====================================================
# VOLUME
# =====================================================

try:
    from pycaw.pycaw import AudioUtilities

    devices = AudioUtilities.GetSpeakers()
    volume = devices.EndpointVolume
    volume_available = True
    print("Windows volume control: ON")

except Exception as e:
    volume_available = False
    print("Volume control unavailable:", e)


# =====================================================
# TIMERS
# =====================================================

last_capture = 0
last_click = 0
last_volume = 0

capture_delay = 2
click_delay = 0.7
volume_delay = 0.5


# =====================================================
# MOUSE SMOOTHING & SENSITIVITY CONFIG
# =====================================================

previous_x = screen_width // 2
previous_y = screen_height // 2

# Higher = smoother (less jitter), Lower = faster reaction (3 to 6 is optimal)
smoothening = 4

# Margin box in camera view (in normalized coordinates 0.0 - 1.0)
margin_x_min, margin_x_max = 0.15, 0.85
margin_y_min, margin_y_max = 0.15, 0.75


# =====================================================
# MAIN LOOP
# =====================================================

while True:
    success, frame = cap.read()

    if not success:
        print("Could not read camera frame.")
        time.sleep(0.1)
        continue

    # Mirror camera
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    # Draw active tracking box on the webcam preview
    cv2.rectangle(
        frame,
        (int(margin_x_min * w), int(margin_y_min * h)),
        (int(margin_x_max * w), int(margin_y_max * h)),
        (0, 255, 0),
        2
    )

    # =================================================
    # HAND DETECTION
    # =================================================

    frame, landmarks = hand_detector.detect_hand(frame)
    gesture = "NO HAND"

    # =================================================
    # IF HAND FOUND
    # =================================================

    if landmarks:
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]

        index_pip = landmarks[6]
        middle_pip = landmarks[10]
        ring_pip = landmarks[14]
        pinky_pip = landmarks[18]

        # -------------------------------------------------
        # FINGER DETECTION
        # -------------------------------------------------
        index_up = index_tip.y < index_pip.y
        middle_up = middle_tip.y < middle_pip.y
        ring_up = ring_tip.y < ring_pip.y
        pinky_up = pinky_tip.y < pinky_pip.y

        # -------------------------------------------------
        # PINCH
        # -------------------------------------------------
        dx = thumb_tip.x - index_tip.x
        dy = thumb_tip.y - index_tip.y
        distance = math.sqrt(dx * dx + dy * dy)
        pinch = distance < 0.05

        # -------------------------------------------------
        # THUMB
        # -------------------------------------------------
        thumb_up = thumb_tip.y < landmarks[3].y

        # =================================================
        # THUMBS UP -> CAPTURE
        # =================================================
        if (
            thumb_up
            and not index_up
            and not middle_up
            and not ring_up
            and not pinky_up
            and not pinch
        ):
            gesture = "THUMBS UP - CAPTURE"
            now = time.time()

            if now - last_capture > capture_delay:
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(desktop, f"hand_capture_{timestamp}.jpg")

                cv2.imwrite(filename, frame)
                print("PHOTO SAVED:", filename)
                last_capture = now

        # =================================================
        # PINCH -> CLICK
        # =================================================
        elif pinch:
            gesture = "PINCH - CLICK"
            now = time.time()

            if now - last_click > click_delay:
                pyautogui.click()
                print("LEFT CLICK")
                last_click = now

        # =================================================
        # INDEX -> MOUSE TRACKING
        # =================================================
        elif (
            index_up
            and not middle_up
            and not ring_up
            and not pinky_up
        ):
            gesture = "INDEX - MOUSE"

            # Interpolate coordinates with margins to reach full screen bounds
            target_x = np.interp(index_tip.x, (margin_x_min, margin_x_max), (0, screen_width))
            target_y = np.interp(index_tip.y, (margin_y_min, margin_y_max), (0, screen_height))

            # Smooth movement
            current_x = previous_x + (target_x - previous_x) / smoothening
            current_y = previous_y + (target_y - previous_y) / smoothening

            # Clamp coordinates within actual display limits
            clamped_x = max(0, min(screen_width - 1, int(current_x)))
            clamped_y = max(0, min(screen_height - 1, int(current_y)))

            pyautogui.moveTo(clamped_x, clamped_y)

            previous_x = current_x
            previous_y = current_y

        # =================================================
        # TWO FINGERS -> VOLUME UP
        # =================================================
        elif (
            index_up
            and middle_up
            and not ring_up
            and not pinky_up
        ):
            gesture = "TWO FINGERS - VOLUME UP"
            now = time.time()

            if now - last_volume > volume_delay:
                if volume_available:
                    current = volume.GetMasterVolumeLevelScalar()
                    new_volume = min(1.0, current + 0.05)
                    volume.SetMasterVolumeLevelScalar(new_volume, None)
                    print("VOLUME:", int(new_volume * 100), "%")
                last_volume = now

        # =================================================
        # FIST -> VOLUME DOWN
        # =================================================
        elif (
            not index_up
            and not middle_up
            and not ring_up
            and not pinky_up
        ):
            gesture = "FIST - VOLUME DOWN"
            now = time.time()

            if now - last_volume > volume_delay:
                if volume_available:
                    current = volume.GetMasterVolumeLevelScalar()
                    new_volume = max(0.0, current - 0.05)
                    volume.SetMasterVolumeLevelScalar(new_volume, None)
                    print("VOLUME:", int(new_volume * 100), "%")
                last_volume = now

        # =================================================
        # OPEN HAND
        # =================================================
        elif (
            index_up
            and middle_up
            and ring_up
            and pinky_up
        ):
            gesture = "OPEN HAND"

    # =====================================================
    # DISPLAY
    # =====================================================

    cv2.putText(frame, "Gesture: " + gesture, (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(frame, "INDEX = Mouse", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, "PINCH = Click", (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, "THUMB = Capture", (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, "2 Fingers = Volume Up", (20, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, "Fist = Volume Down", (20, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, "Press Q to Exit", (20, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # =====================================================
    # SHOW CAMERA
    # =====================================================

    cv2.imshow("Hand Gesture Computer Controller", frame)

    # =====================================================
    # KEYBOARD
    # =====================================================

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        print("Q pressed. Closing...")
        break


# =====================================================
# CLEANUP
# =====================================================

cap.release()
cv2.destroyAllWindows()
print("Camera closed.")