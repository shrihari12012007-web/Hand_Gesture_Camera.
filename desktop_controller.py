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

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

screen_width, screen_height = pyautogui.size()
print(f"OS: {platform.system()} | Combined 1 & 2 Hand Controller Active | Screen: {screen_width}x{screen_height}")


def press_search():
    if IS_MAC:
        pyautogui.hotkey("command", "space")
    else:
        pyautogui.hotkey("win", "s")


def switch_desktop(direction):
    if IS_MAC:
        pyautogui.hotkey("ctrl", direction)
    else:
        pyautogui.hotkey("ctrl", "win", direction)


def open_task_view():
    if IS_MAC:
        pyautogui.hotkey("ctrl", "up")
    else:
        pyautogui.hotkey("win", "tab")


def show_desktop():
    if IS_MAC:
        pyautogui.hotkey("command", "f3")
    else:
        pyautogui.hotkey("win", "d")


def zoom_in():
    if IS_MAC:
        pyautogui.hotkey("command", "=")
    else:
        pyautogui.hotkey("ctrl", "=")


def zoom_out():
    if IS_MAC:
        pyautogui.hotkey("command", "-")
    else:
        pyautogui.hotkey("ctrl", "-")


def save_screenshot(prefix="screenshot"):
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
    filename = os.path.join(save_dir, f"{prefix}_{timestamp}.png")
    pyautogui.screenshot().save(filename)
    print(f"ACTION: Screenshot saved -> {filename}")


# =====================================================
# CAMERA & DETECTOR SETUP
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

cam_width, cam_height = 1280, 720
cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_height)
time.sleep(1)

hand_detector = HandGesture(max_num_hands=2, min_detection_confidence=0.4, min_tracking_confidence=0.4)

# =====================================================
# TIMERS & COOLDOWNS
# =====================================================

last_screenshot = 0
last_click = 0
last_volume = 0
last_swipe = 0
last_search = 0
last_zoom = 0
last_task_view = 0

screenshot_delay = 2.0
click_delay = 0.4
volume_delay = 0.22
swipe_delay = 0.75
search_delay = 1.5
zoom_delay = 0.22
task_view_delay = 2.0

# Mouse smoothing config
previous_x = screen_width // 2
previous_y = screen_height // 2
smoothening = 3
deadzone = 2
margin_x_min, margin_x_max = 0.18, 0.82
margin_y_min, margin_y_max = 0.18, 0.75

# State trackers
swipe_start_x = None
swipe_start_y = None
prev_zoom_dist = None
prev_two_palm_y = None

# =====================================================
# MAIN LOOP
# =====================================================

while True:
    success, frame = cap.read()
    if not success:
        time.sleep(0.01)
        continue

    frame = cv2.flip(frame, 1)
    frame, all_hands = hand_detector.detect_hand(frame)

    gesture = "NO HAND"
    now = time.time()

    # =================================================
    # MODE 1: TWO HANDS ACTIVE
    # =================================================
    if len(all_hands) == 2:
        # Reset 1-hand trackers
        swipe_start_x = None
        swipe_start_y = None

        # Sort left to right by wrist X coordinate
        sorted_hands = sorted(all_hands, key=lambda h: h[0].x)
        lh = sorted_hands[0]
        rh = sorted_hands[1]

        # Finger extensions: Left Hand
        lh_index_up = lh[8].y < lh[6].y
        lh_middle_up = lh[12].y < lh[10].y
        lh_ring_up = lh[16].y < lh[14].y
        lh_pinky_up = lh[20].y < lh[18].y
        lh_palm = lh_index_up and lh_middle_up and lh_ring_up and lh_pinky_up
        lh_fist = (not lh_index_up) and (not lh_middle_up) and (not lh_ring_up) and (not lh_pinky_up)
        lh_pinch = math.hypot(lh[4].x - lh[8].x, lh[4].y - lh[8].y) < 0.06

        # Finger extensions: Right Hand
        rh_index_up = rh[8].y < rh[6].y
        rh_middle_up = rh[12].y < rh[10].y
        rh_ring_up = rh[16].y < rh[14].y
        rh_pinky_up = rh[20].y < rh[18].y
        rh_palm = rh_index_up and rh_middle_up and rh_ring_up and rh_pinky_up
        rh_fist = (not rh_index_up) and (not rh_middle_up) and (not rh_ring_up) and (not rh_pinky_up)
        rh_pinch = math.hypot(rh[4].x - rh[8].x, rh[4].y - rh[8].y) < 0.06

        # 1. Dual Pinch -> Screenshot
        if lh_pinch and rh_pinch:
            gesture = "2 HANDS: DUAL PINCH SCREENSHOT"
            if now - last_screenshot > screenshot_delay:
                save_screenshot("dual_screenshot")
                last_screenshot = now

        # 2. Dual Fists -> Task View
        elif lh_fist and rh_fist:
            gesture = "2 HANDS: DUAL FISTS (TASK VIEW)"
            if now - last_task_view > task_view_delay:
                open_task_view()
                print("ACTION: Task View")
                last_task_view = now

        # 3. Dual Palms -> Volume Up / Down
        elif lh_palm and rh_palm:
            avg_y = (lh[0].y + rh[0].y) / 2.0
            if prev_two_palm_y is not None:
                dy = avg_y - prev_two_palm_y
                if dy < -0.04 and (now - last_volume > volume_delay):
                    pyautogui.press("volumeup", presses=2)
                    gesture = "2 HANDS: PALMS UP (VOL +)"
                    last_volume = now
                    prev_two_palm_y = avg_y
                elif dy > 0.04 and (now - last_volume > volume_delay):
                    pyautogui.press("volumedown", presses=2)
                    gesture = "2 HANDS: PALMS DOWN (VOL -)"
                    last_volume = now
                    prev_two_palm_y = avg_y
                else:
                    gesture = "2 HANDS: PALMS ACTIVE"
            else:
                prev_two_palm_y = avg_y
                gesture = "2 HANDS: PALMS DETECTED"
            prev_zoom_dist = None

        # 4. Dual Index Fingers -> Zoom In / Zoom Out
        elif lh_index_up and rh_index_up and (not lh_middle_up) and (not rh_middle_up):
            current_dist = math.hypot(lh[8].x - rh[8].x, lh[8].y - rh[8].y)
            if prev_zoom_dist is not None:
                delta_d = current_dist - prev_zoom_dist
                if delta_d > 0.03 and (now - last_zoom > zoom_delay):
                    zoom_in()
                    gesture = "2 HANDS: SPREAD (ZOOM IN +)"
                    last_zoom = now
                    prev_zoom_dist = current_dist
                elif delta_d < -0.03 and (now - last_zoom > zoom_delay):
                    zoom_out()
                    gesture = "2 HANDS: PINCH (ZOOM OUT -)"
                    last_zoom = now
                    prev_zoom_dist = current_dist
                else:
                    gesture = "2 HANDS: ZOOM READY"
            else:
                prev_zoom_dist = current_dist
                gesture = "2 HANDS: INDEX FINGERS DETECTED"
            prev_two_palm_y = None
        else:
            prev_zoom_dist = None
            prev_two_palm_y = None
            gesture = "2 HANDS ACTIVE"

    # =================================================
    # MODE 2: SINGLE HAND ACTIVE
    # =================================================
    elif len(all_hands) == 1:
        prev_zoom_dist = None
        prev_two_palm_y = None

        landmarks = all_hands[0]
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        middle_mcp = landmarks[9]

        index_up = index_tip.y < landmarks[6].y
        middle_up = middle_tip.y < landmarks[10].y
        ring_up = ring_tip.y < landmarks[14].y
        pinky_up = pinky_tip.y < landmarks[18].y

        index_down = index_tip.y > landmarks[6].y or index_tip.y > landmarks[5].y
        middle_down = middle_tip.y > landmarks[10].y or middle_tip.y > landmarks[9].y
        ring_down = ring_tip.y > landmarks[14].y or ring_tip.y > landmarks[13].y
        pinky_down = pinky_tip.y > landmarks[18].y or pinky_tip.y > landmarks[17].y
        is_fist = index_down and middle_down and ring_down and pinky_down

        dist_thumb_index = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
        pinch_thumb_index = dist_thumb_index < 0.055
        thumb_up = (thumb_tip.y < landmarks[3].y) and (thumb_tip.y < landmarks[2].y)

        # 1. Swipes (Open Palm / 4 Fingers)
        if index_up and middle_up and ring_up and pinky_up:
            gesture = "1 HAND: 4 FINGERS / PALM"
            if swipe_start_x is None or swipe_start_y is None:
                swipe_start_x = middle_mcp.x
                swipe_start_y = middle_mcp.y
            else:
                diff_x = middle_mcp.x - swipe_start_x
                diff_y = middle_mcp.y - swipe_start_y
                if now - last_swipe > swipe_delay:
                    if diff_y < -0.15:
                        open_task_view()
                        print("ACTION: Task View")
                        last_swipe = now
                        swipe_start_x, swipe_start_y = None, None
                    elif diff_y > 0.15:
                        show_desktop()
                        print("ACTION: Show Desktop")
                        last_swipe = now
                        swipe_start_x, swipe_start_y = None, None
                    elif diff_x > 0.12:
                        switch_desktop("right")
                        print("ACTION: Next Desktop")
                        last_swipe = now
                        swipe_start_x, swipe_start_y = None, None
                    elif diff_x < -0.12:
                        switch_desktop("left")
                        print("ACTION: Previous Desktop")
                        last_swipe = now
                        swipe_start_x, swipe_start_y = None, None
        else:
            swipe_start_x = None
            swipe_start_y = None

            # 2. Screenshot (Middle Finger Only)
            if middle_up and not index_up and not ring_up and not pinky_up and not pinch_thumb_index:
                gesture = "1 HAND: MIDDLE FINGER (SCREENSHOT)"
                if now - last_screenshot > screenshot_delay:
                    save_screenshot("screenshot")
                    last_screenshot = now

            # 3. Search (Pinky Finger Only)
            elif pinky_up and not index_up and not middle_up and not ring_up and not pinch_thumb_index:
                gesture = "1 HAND: PINKY (SEARCH)"
                if now - last_search > search_delay:
                    press_search()
                    print("ACTION: Search")
                    last_search = now

            # 4. Left Click (Pinch)
            elif pinch_thumb_index:
                gesture = "1 HAND: PINCH (LEFT CLICK)"
                if now - last_click > click_delay:
                    pyautogui.click()
                    print("ACTION: Left Click")
                    last_click = now

            # 5. Volume Down (Fist)
            elif is_fist and not thumb_up:
                gesture = "1 HAND: FIST (VOLUME -)"
                if now - last_volume > volume_delay:
                    pyautogui.press("volumedown", presses=2)
                    print("VOLUME: DOWN (-)")
                    last_volume = now

            # 6. Volume Up (Two Fingers)
            elif index_up and middle_up and not ring_up and not pinky_up:
                gesture = "1 HAND: 2 FINGERS (VOLUME +)"
                if now - last_volume > volume_delay:
                    pyautogui.press("volumeup", presses=2)
                    print("VOLUME: UP (+)")
                    last_volume = now

            # 7. Mouse Movement (Index Finger Only)
            elif index_up and not middle_up and not ring_up and not pinky_up:
                gesture = "1 HAND: INDEX (MOUSE)"
                target_x = np.interp(index_tip.x, (margin_x_min, margin_x_max), (0, screen_width))
                target_y = np.interp(index_tip.y, (margin_y_min, margin_y_max), (0, screen_height))

                current_x = previous_x + (target_x - previous_x) / smoothening
                current_y = previous_y + (target_y - previous_y) / smoothening

                if abs(current_x - previous_x) > deadzone or abs(current_y - previous_y) > deadzone:
                    clamped_x = max(0, min(screen_width - 1, int(current_x)))
                    clamped_y = max(0, min(screen_height - 1, int(current_y)))
                    pyautogui.moveTo(clamped_x, clamped_y)
                    previous_x, previous_y = current_x, current_y
    else:
        # No hands visible
        prev_zoom_dist = None
        prev_two_palm_y = None
        swipe_start_x = None
        swipe_start_y = None

    # =====================================================
    # ON-SCREEN HUD
    # =====================================================
    cv2.putText(frame, f"Active: {gesture}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.70, (0, 255, 0), 2)
    cv2.putText(frame, "[1 Hand] Index: Mouse | Pinch: Click | 2 Fingers/Fist: Vol", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.putText(frame, "[2 Hands] Both Index: Zoom | Both Palms: Vol | Both Fists: TaskView", (20, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    cv2.putText(frame, "Press Q to Exit", (20, 115), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (0, 0, 255), 2)

    cv2.imshow("Smart Hand Gesture Controller", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
print("Camera closed.")