import cv2
import os
import sys
import time
import math
import platform
import numpy as np
import pyautogui
from datetime import datetime
from hand_gesture import HandGesture


# =====================================================
# OS PLATFORM CONFIGURATION
# =====================================================

IS_MAC = platform.system() == "Darwin"
IS_WINDOWS = platform.system() == "Windows"


def press_search():
    """Trigger System Search (Win + S on Windows, Command + Space on Mac)"""
    if IS_MAC:
        pyautogui.hotkey("command", "space")
    else:
        pyautogui.hotkey("win", "s")


def switch_desktop(direction):
    """Switch virtual desktops"""
    if IS_MAC:
        pyautogui.hotkey("ctrl", direction)
    else:
        pyautogui.hotkey("ctrl", "win", direction)


def open_task_view():
    """Open Task View / Mission Control"""
    if IS_MAC:
        pyautogui.hotkey("ctrl", "up")
    else:
        pyautogui.hotkey("win", "tab")


def show_desktop():
    """Show / Hide Desktop"""
    if IS_MAC:
        pyautogui.hotkey("command", "f3")
    else:
        pyautogui.hotkey("win", "d")


# =====================================================
# SETTINGS
# =====================================================

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

screen_width, screen_height = pyautogui.size()
print(f"OS: {platform.system()} | Screen size: {screen_width} x {screen_height}")


# =====================================================
# CAMERA SETUP
# =====================================================

print("Starting camera...")
if IS_WINDOWS:
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
else:
    cap = cv2.VideoCapture(0)

if not cap.isOpened():
    cap.release()
    cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("ERROR: Camera could not be opened.")
    sys.exit()

print("Camera opened successfully!")

cam_width, cam_height = 1280, 720
cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_height)

time.sleep(1)


# =====================================================
# HAND DETECTOR INITIALIZATION
# =====================================================

hand_detector = HandGesture()


# =====================================================
# TIMERS & COOLDOWNS
# =====================================================

last_screenshot = 0
last_click = 0
last_volume = 0
last_swipe = 0
last_search = 0

screenshot_delay = 2.0
click_delay = 0.4
volume_delay = 0.25
swipe_delay = 0.75
search_delay = 1.5

# Swipe coordinates tracking
swipe_start_x = None
swipe_start_y = None


# =====================================================
# MOUSE SMOOTHING & BOUNDS CONFIG
# =====================================================

previous_x = screen_width // 2
previous_y = screen_height // 2

smoothening = 3
deadzone = 2

# Screen reach margins (normalized 0.0 to 1.0)
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

    # Mirror camera feed horizontally
    frame = cv2.flip(frame, 1)

    # Detect hand landmarks
    frame, landmarks = hand_detector.detect_hand(frame)
    gesture = "NO HAND"

    if landmarks:
        wrist = landmarks[0]
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]

        index_mcp = landmarks[5]
        middle_mcp = landmarks[9]
        ring_mcp = landmarks[13]
        pinky_mcp = landmarks[17]

        index_pip = landmarks[6]
        middle_pip = landmarks[10]
        ring_pip = landmarks[14]
        pinky_pip = landmarks[18]

        # -------------------------------------------------
        # FINGER EXTENSION STATUS
        # -------------------------------------------------
        index_up = index_tip.y < index_pip.y
        middle_up = middle_tip.y < middle_pip.y
        ring_up = ring_tip.y < ring_pip.y
        pinky_up = pinky_tip.y < pinky_pip.y

        # Fist detection
        index_down = index_tip.y > index_pip.y or index_tip.y > index_mcp.y
        middle_down = middle_tip.y > middle_pip.y or middle_tip.y > middle_mcp.y
        ring_down = ring_tip.y > ring_pip.y or ring_tip.y > ring_mcp.y
        pinky_down = pinky_tip.y > pinky_pip.y or pinky_tip.y > pinky_mcp.y
        is_fist = index_down and middle_down and ring_down and pinky_down

        # Left Click Pinch (Thumb + Index)
        dist_thumb_index = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
        pinch_thumb_index = dist_thumb_index < 0.055

        thumb_up = (thumb_tip.y < landmarks[3].y) and (thumb_tip.y < landmarks[2].y)

        now = time.time()

        # =================================================
        # 1. 4 FINGERS / OPEN PALM GESTURES (SWIPES)
        # =================================================
        if index_up and middle_up and ring_up and pinky_up:
            gesture = "4 FINGERS / PALM"

            if swipe_start_x is None or swipe_start_y is None:
                swipe_start_x = middle_mcp.x
                swipe_start_y = middle_mcp.y
            else:
                diff_x = middle_mcp.x - swipe_start_x
                diff_y = middle_mcp.y - swipe_start_y

                if now - last_swipe > swipe_delay:
                    # Swipe Up -> Task View / Mission Control
                    if diff_y < -0.15:
                        open_task_view()
                        print("ACTION: Task View")
                        last_swipe = now
                        swipe_start_x = None
                        swipe_start_y = None

                    # Swipe Down -> Show Desktop
                    elif diff_y > 0.15:
                        show_desktop()
                        print("ACTION: Show Desktop")
                        last_swipe = now
                        swipe_start_x = None
                        swipe_start_y = None

                    # Swipe Right -> Next Virtual Desktop
                    elif diff_x > 0.12:
                        switch_desktop("right")
                        print("ACTION: Next Desktop")
                        last_swipe = now
                        swipe_start_x = None
                        swipe_start_y = None

                    # Swipe Left -> Previous Virtual Desktop
                    elif diff_x < -0.12:
                        switch_desktop("left")
                        print("ACTION: Previous Desktop")
                        last_swipe = now
                        swipe_start_x = None
                        swipe_start_y = None

        else:
            # Reset swipe coordinates
            swipe_start_x = None
            swipe_start_y = None

            # =============================================
            # 2. MIDDLE FINGER ONLY -> TAKE SCREENSHOT
            # =============================================
            if (
                middle_up
                and not index_up
                and not ring_up
                and not pinky_up
                and not pinch_thumb_index
            ):
                gesture = "MIDDLE FINGER - SCREENSHOT"
                if now - last_screenshot > screenshot_delay:
                    user_home = os.path.expanduser("~")
                    desktop_onedrive = os.path.join(user_home, "OneDrive", "Desktop")
                    desktop_default = os.path.join(user_home, "Desktop")

                    if os.path.exists(desktop_onedrive):
                        save_dir = desktop_onedrive
                    elif os.path.exists(desktop_default):
                        save_dir = desktop_default
                    else:
                        save_dir = os.path.join(os.getcwd(), "screenshots")
                        os.makedirs(save_dir, exist_ok=True)

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = os.path.join(save_dir, f"screenshot_{timestamp}.png")

                    screenshot = pyautogui.screenshot()
                    screenshot.save(filename)

                    print("SCREENSHOT SAVED TO:", filename)
                    last_screenshot = now

            # =============================================
            # 3. PINKY ONLY -> SEARCH (Win+S / Spotlight)
            # =============================================
            elif (
                pinky_up
                and not index_up
                and not middle_up
                and not ring_up
                and not pinch_thumb_index
            ):
                gesture = "PINKY - SEARCH"
                if now - last_search > search_delay:
                    press_search()
                    print("ACTION: Open Search (Win+S / Spotlight)")
                    last_search = now

            # =============================================
            # 4. THUMB + INDEX PINCH -> LEFT CLICK
            # =============================================
            elif pinch_thumb_index:
                gesture = "THUMB+INDEX - LEFT CLICK"
                if now - last_click > click_delay:
                    pyautogui.click()
                    print("LEFT CLICK")
                    last_click = now

            # =============================================
            # 5. FIST -> VOLUME DOWN
            # =============================================
            elif is_fist and not thumb_up:
                gesture = "FIST - VOLUME DOWN"
                if now - last_volume > volume_delay:
                    pyautogui.press("volumedown")
                    pyautogui.press("volumedown")
                    print("VOLUME: DOWN (-)")
                    last_volume = now

            # =============================================
            # 6. 2 FINGERS (INDEX + MIDDLE) -> VOLUME UP
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
                    pyautogui.press("volumeup")
                    print("VOLUME: UP (+)")
                    last_volume = now

            # =============================================
            # 7. INDEX ONLY -> HIGH ACCURACY MOUSE
            # =============================================
            elif (
                index_up
                and not middle_up
                and not ring_up
                and not pinky_up
            ):
                gesture = "INDEX - MOUSE"

                target_x = np.interp(index_tip.x, (margin_x_min, margin_x_max), (0, screen_width))
                target_y = np.interp(index_tip.y, (margin_y_min, margin_y_max), (0, screen_height))

                current_x = previous_x + (target_x - previous_x) / smoothening
                current_y = previous_y + (target_y - previous_y) / smoothening

                if abs(current_x - previous_x) > deadzone or abs(current_y - previous_y) > deadzone:
                    clamped_x = max(0, min(screen_width - 1, int(current_x)))
                    clamped_y = max(0, min(screen_height - 1, int(current_y)))
                    pyautogui.moveTo(clamped_x, clamped_y)

                    previous_x = current_x
                    previous_y = current_y

    # =====================================================
    # HUD / ON-SCREEN INSTRUCTIONS
    # =====================================================

    cv2.putText(frame, f"Gesture: {gesture}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.70, (0, 255, 0), 2)
    cv2.putText(frame, "Index Finger: Move Mouse", (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.putText(frame, "Thumb + Index: Left Click", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.putText(frame, "Pinky Finger: Search (Win+S / Spotlight)", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.putText(frame, "Middle Finger Only: Take Screenshot", (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.putText(frame, "2 Fingers: Volume Up", (20, 135), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.putText(frame, "Fist: Volume Down", (20, 155), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.putText(frame, "4 Fingers/Palm L/R: Switch Desktop", (20, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.putText(frame, "4 Fingers Up/Down: TaskView / Desktop", (20, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.putText(frame, "Press Q to Exit", (20, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 0, 255), 2)

    cv2.imshow("Hand Gesture Controller", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("Camera closed.")