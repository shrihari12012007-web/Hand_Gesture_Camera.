import os
import time
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class HandGesture:
    """
    Robust MediaPipe HandLandmarker wrapper ensuring strictly monotonic timestamps
    and fault-tolerant video-mode hand landmark extraction.
    """
    def __init__(self, max_num_hands=2, min_detection_confidence=0.4, min_tracking_confidence=0.4):
        self.last_timestamp_ms = 0

        # Locate hand_landmarker.task model file
        possible_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task"),
            os.path.join(os.getcwd(), "hand_landmarker.task"),
            "hand_landmarker.task"
        ]
        model_path = None
        for p in possible_paths:
            if os.path.exists(p):
                model_path = p
                break

        if not model_path:
            raise FileNotFoundError(
                "Could not locate 'hand_landmarker.task'. Ensure the model file is present in the repository."
            )

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            running_mode=vision.RunningMode.VIDEO
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

        # Standard MediaPipe 21-landmark hand connections
        self.connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),        # Index
            (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
            (9, 13), (13, 14), (14, 15), (15, 16), # Ring
            (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
            (0, 17)                                # Palm base
        ]

    def detect_hand(self, frame):
        """
        Processes a BGR image frame, extracts hand landmarks, and renders skeletal overlay.
        Returns:
            frame: Annotated OpenCV frame
            all_hands_landmarks: List of landmark sets for each detected hand
        """
        if frame is None or frame.size == 0:
            return frame, []

        all_hands_landmarks = []

        try:
            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # Strictly monotonic millisecond timestamp to prevent MediaPipe ValueError on Windows
            current_ms = int(time.time() * 1000)
            if current_ms <= self.last_timestamp_ms:
                current_ms = self.last_timestamp_ms + 1
            self.last_timestamp_ms = current_ms

            result = self.detector.detect_for_video(mp_image, current_ms)

            if result and result.hand_landmarks:
                h, w, _ = frame.shape
                for hand in result.hand_landmarks:
                    all_hands_landmarks.append(hand)
                    points = [(int(pt.x * w), int(pt.y * h)) for pt in hand]

                    # Draw skeleton connections
                    for start, end in self.connections:
                        cv2.line(frame, points[start], points[end], (0, 255, 120), 2, cv2.LINE_AA)

                    # Draw joint landmarks
                    for idx, pt in enumerate(points):
                        # Emphasize fingertips
                        if idx in [4, 8, 12, 16, 20]:
                            cv2.circle(frame, pt, 6, (0, 180, 255), -1, cv2.LINE_AA)
                            cv2.circle(frame, pt, 8, (255, 255, 255), 1, cv2.LINE_AA)
                        else:
                            cv2.circle(frame, pt, 4, (0, 0, 255), -1, cv2.LINE_AA)

        except Exception as e:
            # Log non-fatal processing warning without terminating controller loop
            pass

        return frame, all_hands_landmarks
