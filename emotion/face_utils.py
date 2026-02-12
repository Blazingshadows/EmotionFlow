import cv2
import mediapipe as mp
import numpy as np


class FaceDetector:
    """
    Fast, robust face detection using Mediapipe.
    Returns cropped face aligned to model input size.
    """

    def __init__(self, target_size=(48, 48)):
        self.target_size = target_size

        self.mp_face = mp.solutions.face_detection
        self.detector = self.mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.5)

    def get_face(self, frame):
        """
        Input:
            frame (BGR image)
        Output:
            cropped_face (48x48 or target size)
            None if no face detected
        """

        h, w, _ = frame.shape

        results = self.detector.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        if not results.detections:
            return None  # No face detected

        # Pick the strongest detection
        detection = results.detections[0]
        bbox = detection.location_data.relative_bounding_box

        x = int(bbox.xmin * w)
        y = int(bbox.ymin * h)
        width = int(bbox.width * w)
        height = int(bbox.height * h)

        # Ensure valid box
        x = max(0, x)
        y = max(0, y)
        x2 = min(w, x + width)
        y2 = min(h, y + height)

        face = frame[y:y2, x:x2]

        if face.size == 0:
            return None

        # Resize to model input (48x48 or 224x224 depending on target)
        face_gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        face_resized = cv2.resize(face_gray, self.target_size)

        # Normalize
        face_norm = face_resized.astype("float32") / 255.0

        # Final shape: (48,48,1)
        face_norm = np.expand_dims(face_norm, axis=-1)

        return face_norm
