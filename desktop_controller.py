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

time.sleep(1)


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
# TIMERS & SWIPE STATE
# =====================================================

last_capture = 0
last_click = 0
last_volume = 0
last_swipe = 0

capture_delay = 2.0
click_delay = 0.5
volume_delay = 0.4
swipe_delay = 0.8  # Cooldown between swipe gestures

# Swipe tracking variables
swipe_start_x = None
swipe_start_y = None


# =====================================================
# MOUSE SMOOTHING & SENSITIVITY CONFIG
# =====================================================

previous_x = screen_width // 2
previous_y = screen_height // 2

smoothening = 3  # Lower value = sharper, more responsive tracking
deadzone = 2     # Pixel threshold: ignores involuntary hand twitches

# Screen reach margins (normalized 0.0 - 1.0)
margin_x_min, margin_x_max = 0.18, 0.82
margin_y_min, margin_y_max = 0.18, 0.75


# =====================================================
# MAIN LOOP
# =====================================================

while True:
    success, frame = cap.read()

    if not success:
        time.sleep(0.01)
        continue

    # Mirror camera
    frame = cv2.flip(frame, 1)

    # =================================================
    # HAND DETECTION
    # =================================================

    frame, landmarks = hand_detector.detect_hand(frame)
    gesture = "NO HAND"

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
        pinch = distance < 0.055

        # -------------------------------------------------
        # THUMB
        # -------------------------------------------------
        thumb_up = thumb_tip.y < landmarks[3].y
        now = time.time()

        # =================================================
        # 4 FINGERS -> SWIPE (TASK VIEW / DESKTOP / APP SWITCH)
        # =================================================
        if index_up and middle_up and ring_up and pinky_up:
            gesture = "4 FINGERS - GESTURE"

            if swipe_start_x is None or swipe_start_y is None:
                swipe_start_x = middle_tip.x
                swipe_start_y = middle_tip.y
            else:
                diff_x = middle_tip.x - swipe_start_x
                diff_y = middle_tip.y - swipe_start_y

                if now - last_swipe > swipe_delay:
                    # Swipe Up -> Task View
                    if diff_y < -0.15:
                        pyautogui.hotkey("win", "tab")
                        print("ACTION: Task View (Win + Tab)")
                        last_swipe = now
                        swipe_start_x, swipe_start_y = None, None

                    # Swipe Down -> Show Desktop
                    elif diff_y > 0.15:
                        pyautogui.hotkey("win", "d")
                        print("ACTION: Show Desktop (Win + D)")
                        last_swipe = now
                        swipe_start_x, swipe_start_y = None, None

                    # Swipe Left / Right -> Alt + Tab
                    elif diff_x > 0.15:
                        pyautogui.hotkey("alt", "tab")
                        print("ACTION: App Switch (Alt + Tab)")
                        last_swipe = now
                        swipe_start_x, swipe_start_y = None, None
                    elif diff_x < -0.15:
                        pyautogui.hotkey("alt", "shift", "tab")
                        print("ACTION: Previous App (Alt + Shift + Tab)")
                        last_swipe = now
                        swipe_start_x, swipe_start_y = None, None

        # =================================================
        # 3 FINGERS -> SWIPE DESKTOP (VIRTUAL WORKSPACES)
        # =================================================
        elif index_up and middle_up and ring_up and not pinky_up:
            gesture = "3 FINGERS - SWIPE DESKTOP"

            if swipe_start_x is None or swipe_start_y is None:
                swipe_start_x = middle_tip.x
                swipe_start_y = middle_tip.y
            else:
                diff_x = middle_tip.x - swipe_start_x

                if now - last_swipe > swipe_delay:
                    # Swipe Right -> Next Desktop
                    if diff_x > 0.12:
                        pyautogui.hotkey("ctrl", "win", "right")
                        print("ACTION: Switch to Next Desktop")
                        last_swipe = now
                        swipe_start_x, swipe_start_y = None, None

                    # Swipe Left -> Previous Desktop
                    elif diff_x < -0.12:
                        pyautogui.hotkey("ctrl", "win", "left")
                        print("ACTION: Switch to Previous Desktop")
                        last_swipe = now
                        swipe_start_x, swipe_start_y = None, None

        else:
            # Reset swipe coordinates whenever leaving 3-finger / 4-finger modes
            swipe_start_x = None
            swipe_start_y = None

            # =============================================
            # THUMBS UP -> SCREENSHOT CAPTURE
            # =============================================
            if (
                thumb_up
                and not index_up
                and not middle_up
                and not ring_up
                and not pinky_up
                and not pinch
            ):
                gesture = "THUMBS UP - CAPTURE"
                if now - last_capture > capture_delay:
                    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(desktop, f"hand_capture_{timestamp}.jpg")

                    cv2.imwrite(filename, frame)
                    print("PHOTO SAVED:", filename)
                    last_capture = now

            # =============================================
            # PINCH -> CLICK
            # =============================================
            elif pinch:
                gesture = "PINCH - CLICK"
                if now - last_click > click_delay:
                    pyautogui.click()
                    print("LEFT CLICK")
                    last_click = now

            # =============================================
            # INDEX ONLY -> HIGH ACCURACY MOUSE
            # =============================================
            elif (
                index_up
                and not middle_up
                and not ring_up
                and not pinky_up
            ):
                gesture = "INDEX - MOUSE"

                # Map index coordinates across bounds
                target_x = np.interp(index_tip.x, (margin_x_min, margin_x_max), (0, screen_width))
                target_y = np.interp(index_tip.y, (margin_y_min, margin_y_max), (0, screen_height))

                # Smooth movements
                current_x = previous_x + (target_x - previous_x) / smoothening
                current_y = previous_y + (target_y - previous_y) / smoothening

                # Deadzone filter to stop idle trembling
                if abs(current_x - previous_x) > deadzone or abs(current_y - previous_y) > deadzone:
                    clamped_x = max(0, min(screen_width - 1, int(current_x)))
                    clamped_y = max(0, min(screen_height - 1, int(current_y)))
                    pyautogui.moveTo(clamped_x, clamped_y)

                    previous_x = current_x
                    previous_y = current_y

           # =============================================
            # 2 FINGERS -> VOLUME UP
            # =============================================
            elif (
                index_up
                and middle_up
                and not ring_up
                and not pinky_up
            ):
                gesture = "TWO FINGERS - VOLUME UP"
                if now - last_volume > volume_delay:
                    pyautogui.press("volumeup")
                    pyautogui.press("volumeup")  # Twice for a faster volume step
                    print("VOLUME: UP (+)")
                    last_volume = now

            # =============================================
            # FIST -> VOLUME DOWN
            # =============================================
            elif (
                not index_up
                and not middle_up
                and not ring_up
                and not pinky_up
            ):
                gesture = "FIST - VOLUME DOWN"
                if now - last_volume > volume_delay:
                    pyautogui.press("volumedown")
                    pyautogui.press("volumedown")  # Twice for a faster volume step
                    print("VOLUME: DOWN (-)")
                    last_volume = now

    # =====================================================
    # HUD DISPLAY
    # =====================================================

    cv2.putText(frame, f"Gesture: {gesture}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
    cv2.putText(frame, "1 Finger: Accurate Mouse", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    cv2.putText(frame, "Pinch: Click", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    cv2.putText(frame, "3 Fingers: Swipe Desktops (Left/Right)", (20, 125), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    cv2.putText(frame, "4 Fingers: Swipe Up (Task View) / Down (Desktop)", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    cv2.putText(frame, "Press Q to Exit", (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)

    cv2.imshow("Hand Gesture Controller", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("Camera closed.")