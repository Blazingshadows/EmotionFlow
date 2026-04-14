import os
import time
from collections import deque
from typing import Optional, Tuple

import cv2
import numpy as np
import requests

try:
    from mediapipe.tasks.python.core.base_options import BaseOptions
    from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
    from mediapipe.tasks.python.vision.core.image import Image as MpImage, ImageFormat
    MP_TASKS_AVAILABLE = True
except Exception:
    MP_TASKS_AVAILABLE = False


class GestureDetector:
    def __init__(self):
        self.enabled = False
        self.hand_landmarker = None
        self.rock_votes = deque(maxlen=5)
        self.gesture_votes = deque(maxlen=7)
        self.min_votes = 3
        self._timestamp_ms = int(time.time() * 1000)

        self.model_path = os.environ.get(
            "HAND_LANDMARKER_MODEL_PATH",
            os.path.join("assets", "hand_landmarker.task"),
        )

        if not MP_TASKS_AVAILABLE:
            print("[GestureDetector] MediaPipe Tasks API unavailable; gesture detection disabled.")
            return

        if not self._ensure_model_file():
            print("[GestureDetector] Hand landmarker model unavailable; gesture detection disabled.")
            return

        try:
            options = HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=self.model_path),
                running_mode=RunningMode.VIDEO,
                num_hands=1,
                min_hand_detection_confidence=0.6,
                min_hand_presence_confidence=0.6,
                min_tracking_confidence=0.6,
            )
            self.hand_landmarker = HandLandmarker.create_from_options(options)
            self.enabled = True
            print(f"[GestureDetector] Hand landmarker loaded from: {self.model_path}")
        except Exception as e:
            print(f"[GestureDetector] Failed to initialize HandLandmarker: {e}")

    def _ensure_model_file(self) -> bool:
        if os.path.exists(self.model_path):
            return True

        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        url = (
            "https://storage.googleapis.com/mediapipe-models/"
            "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
        )

        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            with open(self.model_path, "wb") as model_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        model_file.write(chunk)
            return True
        except Exception as e:
            print(f"[GestureDetector] Could not download hand model: {e}")
            return False

    @staticmethod
    def _finger_extended(landmarks, tip_idx: int, pip_idx: int, mcp_idx: int) -> bool:
        return (
            landmarks[tip_idx].y < landmarks[pip_idx].y
            and landmarks[pip_idx].y < landmarks[mcp_idx].y
        )

    @staticmethod
    def _thumb_out(landmarks, handedness_label: str) -> bool:
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        if handedness_label == "Right":
            return thumb_tip.x < thumb_ip.x
        return thumb_tip.x > thumb_ip.x

    @staticmethod
    def _thumb_up(landmarks) -> bool:
        wrist = landmarks[0]
        thumb_tip = landmarks[4]
        return thumb_tip.y < wrist.y - 0.08 and abs(thumb_tip.x - wrist.x) < 0.25

    @staticmethod
    def _thumb_down(landmarks) -> bool:
        wrist = landmarks[0]
        thumb_tip = landmarks[4]
        return thumb_tip.y > wrist.y + 0.08 and abs(thumb_tip.x - wrist.x) < 0.25

    def _classify_hand(self, hand_landmarks, handedness_label: str) -> Optional[str]:
        landmarks = hand_landmarks

        index_up = self._finger_extended(landmarks, 8, 6, 5)
        middle_up = self._finger_extended(landmarks, 12, 10, 9)
        ring_up = self._finger_extended(landmarks, 16, 14, 13)
        pinky_up = self._finger_extended(landmarks, 20, 18, 17)
        thumb_side = self._thumb_out(landmarks, handedness_label)

        fingers_up = sum([thumb_side, index_up, middle_up, ring_up, pinky_up])

        if self._thumb_up(landmarks) and not index_up and not middle_up and not ring_up and not pinky_up:
            return "ThumbsUp"

        if self._thumb_down(landmarks) and not index_up and not middle_up and not ring_up and not pinky_up:
            return "ThumbsDown"

        # Rock / yo sign: thumb + index + pinky extended, middle and ring folded.
        if thumb_side and index_up and pinky_up and not middle_up and not ring_up:
            return "Rock"

        # Support the user preference for a three-finger yo-like trigger.
        if fingers_up >= 3 and index_up and pinky_up and not middle_up and not ring_up:
            return "Rock"

        return None

    def _smooth_label(self, label: Optional[str]) -> Tuple[Optional[str], float]:
        self.gesture_votes.append(label)
        valid_votes = [vote for vote in self.gesture_votes if vote]
        if len(valid_votes) < self.min_votes:
            return None, 0.0

        counts = {}
        for vote in valid_votes:
            counts[vote] = counts.get(vote, 0) + 1

        best_label, best_count = max(counts.items(), key=lambda item: item[1])
        confidence = best_count / len(valid_votes)
        if confidence >= 0.6:
            return best_label, float(confidence)
        return None, float(confidence)

    def detect_gesture(self, frame) -> Tuple[Optional[str], float]:
        if not self.enabled or self.hand_landmarker is None:
            return None, 0.0
        if frame is None or frame.size == 0:
            return None, 0.0

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = MpImage(image_format=ImageFormat.SRGB, data=np.ascontiguousarray(rgb))

        self._timestamp_ms = max(self._timestamp_ms + 1, int(time.time() * 1000))
        try:
            result = self.hand_landmarker.detect_for_video(mp_image, self._timestamp_ms)
        except Exception as e:
            print(f"[GestureDetector] Hand detection error: {e}")
            return None, 0.0

        if not result.hand_landmarks:
            return self._smooth_label(None)

        handedness_label = "Right"
        if result.handedness and result.handedness[0]:
            first_category = result.handedness[0][0]
            if first_category and first_category.category_name:
                handedness_label = first_category.category_name

        gesture_label = self._classify_hand(result.hand_landmarks[0], handedness_label)
        return self._smooth_label(gesture_label)

    def detect_yo_gesture(self, frame) -> Tuple[bool, float]:
        label, confidence = self.detect_gesture(frame)
        return label == "Rock", confidence
