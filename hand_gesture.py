import os
import time
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class HandGesture:
    def __init__(self, max_num_hands=2, min_detection_confidence=0.4, min_tracking_confidence=0.4):
        model_path = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")
        if not os.path.exists(model_path):
            model_path = "hand_landmarker.task"

        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=max_num_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
            running_mode=vision.RunningMode.VIDEO
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

        self.connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),
            (0, 5), (5, 6), (6, 7), (7, 8),
            (5, 9), (9, 10), (10, 11), (11, 12),
            (9, 13), (13, 14), (14, 15), (15, 16),
            (13, 17), (17, 18), (18, 19), (19, 20),
            (0, 17)
        ]

    def detect_hand(self, frame):
        # Convert BGR directly to RGB without color blowouts
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # Video mode requires monotonic millisecond timestamps for temporal smoothing
        frame_timestamp_ms = int(time.time() * 1000)
        result = self.detector.detect_for_video(mp_image, frame_timestamp_ms)

        all_hands_landmarks = []

        if result.hand_landmarks:
            h, w, _ = frame.shape
            for hand in result.hand_landmarks:
                all_hands_landmarks.append(hand)

                points = [(int(pt.x * w), int(pt.y * h)) for pt in hand]

                # Draw skeleton connections
                for start, end in self.connections:
                    cv2.line(frame, points[start], points[end], (0, 255, 100), 2)

                # Draw joint points
                for pt in points:
                    cv2.circle(frame, pt, 4, (0, 0, 255), -1)

        return frame, all_hands_landmarks