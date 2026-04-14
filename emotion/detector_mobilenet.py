import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import cv2
from collections import deque
from torchvision import models, transforms
from PIL import Image


class EmotionDetectorMobileNet:
    def __init__(self, model_path="checkpoints_affectnet_yolo/mobilenetv2_best.pth"):
        self.labels = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
        self.label_thresholds = {
            "angry": 0.58,
            "disgust": 0.58,
            "fear": 0.60,
            "happy": 0.60,
            "sad": 0.72,
            "surprise": 0.72,
            "neutral": 0.66,
        }
        self.min_margin = 0.12
        self.neutral_margin = 0.16
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.smile_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_smile.xml"
        )
        self.smooth_window = 8
        self.min_frames_for_smooth = 5
        self.conf_threshold = 0.45
        self.emotion_buffer = deque(maxlen=self.smooth_window)
        self.conf_buffer = deque(maxlen=self.smooth_window)
        
        self.model = models.mobilenet_v2(weights=None)
        self.model.classifier[1] = nn.Linear(self.model.last_channel, 7)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()
        
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                               std=[0.229, 0.224, 0.225]),
        ])

    def _predict_from_face(self, face_bgr):
        if face_bgr is None or face_bgr.size == 0:
            return None, 0.0

        face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(face_rgb.astype("uint8"))
        flipped_img = pil_img.transpose(Image.FLIP_LEFT_RIGHT)

        img_tensor = self.transform(pil_img).unsqueeze(0).to(self.device)
        img_tensor_flip = self.transform(flipped_img).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            logits = self.model(img_tensor)
            logits_flip = self.model(img_tensor_flip)
            probs = 0.5 * F.softmax(logits, dim=1)[0] + 0.5 * F.softmax(logits_flip, dim=1)[0]

        topk = torch.topk(probs, k=2)
        idx = int(topk.indices[0].item())
        conf = float(topk.values[0].item())
        second = float(topk.values[1].item()) if topk.values.numel() > 1 else 0.0
        margin = conf - second
        label = self.labels[idx]

        threshold = self.label_thresholds.get(label, 0.65)
        if label == "neutral":
            threshold = max(threshold, 0.68)

        if conf < threshold or margin < (self.neutral_margin if label in {"sad", "surprise", "neutral"} else self.min_margin):
            return None, conf
        
        return label, conf

    def _get_smoothed(self):
        if len(self.emotion_buffer) < self.min_frames_for_smooth:
            return None, 0.0

        score_map = {}
        for e, c in zip(self.emotion_buffer, self.conf_buffer):
            w = c if c >= self.conf_threshold else (0.25 * c)
            score_map[e] = score_map.get(e, 0.0) + w

        if not score_map:
            return None, 0.0

        best_label, best_score = max(score_map.items(), key=lambda x: x[1])
        total = sum(score_map.values())
        return best_label, float(best_score / total) if total > 0 else 0.0

    def predict(self, face_gray):
        if face_gray is None or face_gray.size == 0:
            return None, 0.0
        face_bgr = cv2.cvtColor(face_gray, cv2.COLOR_GRAY2BGR)
        return self._predict_from_face(face_bgr)

    def predict_frame(self, bgr_frame):
        frame = bgr_frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        if len(faces) == 0:
            cv2.putText(
                frame,
                "No face detected",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 0, 200),
                2,
            )
            return "", 0.0, frame

        x, y, w, h = sorted(faces, key=lambda r: r[2] * r[3], reverse=True)[0]
        pad = 0.2
        pad_w = int(w * pad)
        pad_h = int(h * pad)

        x1 = max(0, x - pad_w)
        y1 = max(0, y - pad_h)
        x2 = min(frame.shape[1], x + w + pad_w)
        y2 = min(frame.shape[0], y + h + pad_h)

        face_gray = gray[y1:y2, x1:x2]
        face_bgr = frame[y1:y2, x1:x2]
        label, conf = self._predict_from_face(face_bgr)

        # If a clear smile is present, prevent obvious smile faces
        # from being mislabeled as sad/neutral/fear.
        smile_regions = self.smile_cascade.detectMultiScale(
            face_gray,
            scaleFactor=1.7,
            minNeighbors=22,
            minSize=(25, 25),
        )
        has_smile = len(smile_regions) > 0
        if has_smile and label in {"sad", "neutral", "fear"} and conf < 0.90:
            label = "happy"
            conf = max(conf, 0.62)

        if label:
            self.emotion_buffer.append(label)
            self.conf_buffer.append(conf)

        smoothed_label, smoothed_conf = self._get_smoothed()
        disp_label = smoothed_label if smoothed_label else label
        disp_conf = smoothed_conf if smoothed_label else conf

        if disp_label is None:
            disp_label = "Neutral"
            disp_conf = 0.0

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 0), 2)
        cv2.putText(
            frame,
            f"{disp_label} ({disp_conf:.2f})",
            (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 200, 0),
            2,
        )

        return disp_label, float(disp_conf), frame
