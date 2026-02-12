import os
import cv2
import numpy as np

EMOTION_LABELS = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']

def load_fer2013_from_folders(dataset_path="FER2013"):
    X, y = [], []

    for idx, emotion in enumerate(EMOTION_LABELS):
        emotion_dir = os.path.join(dataset_path, "train", emotion.lower())

        for img_file in os.listdir(emotion_dir):
            if img_file.endswith(".jpg") or img_file.endswith(".png"):
                path = os.path.join(emotion_dir, img_file)
                img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)

                if img is None:
                    continue

                img = cv2.resize(img, (48, 48))
                X.append(img)
                y.append(idx)

    X = np.array(X, dtype="float32") / 255.0
    X = np.expand_dims(X, -1)
    y = np.array(y)

    return X, y
