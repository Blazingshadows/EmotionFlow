import os
import time
import json
from collections import deque, Counter
from typing import Tuple, Optional, Dict

import cv2
import numpy as np
import torch
import torch.nn.functional as F

try:
    from training.minixception_model import MiniXception
except Exception as e:
    raise ImportError("minixception_model not found or has errors.") from e
MODEL_PATH = os.environ.get("MINIX_MODEL_PATH", "assets/minixception_torch.pth")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

EMOTION_LABELS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']

SMOOTH_WINDOW = 15
CONF_THRESHOLD = 0.45  # Increased from 0.35 to require higher confidence
MIN_FRAMES_FOR_SMOOTH = 5  # Increased from 3 to need more consistent frames

HAAR_SCALE = 1.1
HAAR_NEIGHBORS = 5  # Increased for better face detection
PADDING = 0.25  # Increased from 0.20 for more context

# Debug mode - set to True to see prediction details
DEBUG_MODE = os.environ.get("EMOTION_DEBUG", "false").lower() == "true"


def rotate_image(img: np.ndarray, angle: float) -> np.ndarray:
    (h, w) = img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR)


def align_face_using_eyes(gray_face: np.ndarray, eye_cascade) -> np.ndarray:
    eyes = eye_cascade.detectMultiScale(gray_face, scaleFactor=1.05, minNeighbors=3)
    if len(eyes) < 2:
        return gray_face

    eyes = sorted(eyes, key=lambda e: e[2] * e[3], reverse=True)[:2]
    eye_centers = []
    for (ex, ey, ew, eh) in eyes:
        eye_centers.append((ex + ew / 2.0, ey + eh / 2.0))

    if len(eye_centers) < 2:
        return gray_face

    (x1, y1), (x2, y2) = eye_centers
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0:
        return gray_face

    angle = np.degrees(np.arctan2(dy, dx))
    rotated = rotate_image(gray_face, angle)
    return rotated


def weight_vote(emotions: list, confidences: list) -> Tuple[str, float]:
    if not emotions:
        return "", 0.0
    score_map = {}
    for e, c in zip(emotions, confidences):
        score_map[e] = score_map.get(e, 0.0) + float(c)
    best = max(score_map.items(), key=lambda x: x[1])
    total = sum(score_map.values()) if sum(score_map.values()) > 0 else 1.0
    return best[0], float(best[1]) / total


class EmotionDetector:
    def __init__(self,
                 model_path: str = MODEL_PATH,
                 device: str = DEVICE,
                 labels: Optional[list] = None):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model weights not found at: {model_path}")

        self.device = torch.device(device)
        self.model = MiniXception(num_classes=len(EMOTION_LABELS))
        state = torch.load(model_path, map_location=self.device)
        if isinstance(state, dict) and 'state_dict' in state:
            self.model.load_state_dict(state['state_dict'])
        else:
            try:
                self.model.load_state_dict(state)
            except Exception:
                self.model.load_state_dict(state, strict=False)

        self.model.to(self.device)
        self.model.eval()

        self.labels = labels if labels is not None else EMOTION_LABELS
        
        print(f"✓ MiniXception model loaded from: {model_path}")
        print(f"✓ Device: {self.device}")
        print(f"✓ Labels: {self.labels}")

        self.emotion_buffer = deque(maxlen=SMOOTH_WINDOW)
        self.conf_buffer = deque(maxlen=SMOOTH_WINDOW)
        self.timestamp_buffer = deque(maxlen=SMOOTH_WINDOW)

        os.makedirs("session_logs", exist_ok=True)
        self.current_session_file = None
        self.session_active = False

    def start_session_log(self):
        t = time.strftime("%Y%m%d_%H%M%S")
        fname = f"session_logs/session_{t}.jsonl"
        self.current_session_file = open(fname, "a", buffering=1)
        self.session_active = True
        hdr = {"session_start": time.time(), "model": os.path.basename(MODEL_PATH)}
        self.current_session_file.write(json.dumps(hdr) + "\n")
        return fname

    def end_session_log(self):
        if self.current_session_file:
            self.current_session_file.write(json.dumps({"session_end": time.time()}) + "\n")
            self.current_session_file.close()
            self.current_session_file = None
        self.session_active = False

    def log_event(self, emotion: str, confidence: float):
        if not self.session_active or not self.current_session_file:
            return
        rec = {"ts": time.time(), "emotion": emotion, "confidence": float(confidence)}
        self.current_session_file.write(json.dumps(rec) + "\n")

    def predict_frame(self, bgr_frame: np.ndarray) -> Tuple[str, float, np.ndarray]:
        frame = bgr_frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=HAAR_SCALE, minNeighbors=HAAR_NEIGHBORS)
        label = ""
        conf = 0.0

        if len(faces) > 0:
            faces = sorted(faces, key=lambda r: r[2] * r[3], reverse=True)
            (x, y, w, h) = faces[0]

            pad_w = int(w * PADDING)
            pad_h = int(h * PADDING)
            x1 = max(0, x - pad_w)
            y1 = max(0, y - pad_h)
            x2 = min(frame.shape[1], x + w + pad_w)
            y2 = min(frame.shape[0], y + h + pad_h)

            face_patch = gray[y1:y2, x1:x2]

            aligned = align_face_using_eyes(face_patch, self.eye_cascade)

            try:
                face48 = cv2.resize(aligned, (48, 48), interpolation=cv2.INTER_AREA)
            except Exception:
                face48 = cv2.resize(face_patch, (48, 48), interpolation=cv2.INTER_AREA)

            inp = face48.astype("float32") / 255.0
            inp = np.expand_dims(inp, axis=(0, 1))
            inp_tensor = torch.from_numpy(inp).to(self.device)

            with torch.no_grad():
                out = self.model(inp_tensor)
                probs = F.softmax(out, dim=1).cpu().numpy().flatten()
                idx = int(np.argmax(probs))
                conf = float(probs[idx])
                label = self.labels[idx] if idx < len(self.labels) else str(idx)
                
                # Debug output
                if DEBUG_MODE:
                    print(f"Raw predictions: {dict(zip(EMOTION_LABELS, probs))}")
                    print(f"Detected: {label} ({conf:.3f})")

            self.emotion_buffer.append(label)
            self.conf_buffer.append(conf)
            self.timestamp_buffer.append(time.time())

            smoothed_label, smoothed_conf = self._get_smoothed_output()

            disp_label = smoothed_label if smoothed_label else label
            disp_conf = smoothed_conf if smoothed_label else conf

            text = f"{disp_label}  ({disp_conf:.2f})"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 0), 2)
            cv2.putText(frame, text, (x1, max(15, y1 - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 0), 2)

            if self.session_active:
                now = time.time()
                last_ts = self.timestamp_buffer[-1] if len(self.timestamp_buffer) > 0 else now
                if len(self.timestamp_buffer) >= 1 and (now - self.timestamp_buffer[0]) >= 1.0:
                    if smoothed_label:
                        self.log_event(smoothed_label, smoothed_conf)
                    else:
                        self.log_event(label, conf)

            return (disp_label, float(disp_conf), frame)

        cv2.putText(frame, "No face detected", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 200), 2)
        return ("", 0.0, frame)

    def _get_smoothed_output(self) -> Tuple[Optional[str], float]:
        if len(self.emotion_buffer) < MIN_FRAMES_FOR_SMOOTH:
            return (None, 0.0)

        emotions = list(self.emotion_buffer)
        confs = list(self.conf_buffer)

        weights = [c if c >= CONF_THRESHOLD else (c * 0.25) for c in confs]

        score_map = {}
        for e, w in zip(emotions, weights):
            score_map[e] = score_map.get(e, 0.0) + w

        best_emotion = max(score_map.items(), key=lambda x: x[1])
        total = sum(score_map.values()) if sum(score_map.values()) > 0 else 1.0
        return (best_emotion[0], float(best_emotion[1] / total))


if __name__ == "__main__":
    det = EmotionDetector()
    cap = cv2.VideoCapture(0)
    print("Press q to quit")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        label, conf, ann = det.predict_frame(frame)
        cv2.imshow("ann", ann)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
