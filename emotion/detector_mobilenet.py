import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from torchvision import models, transforms
from PIL import Image


class EmotionDetectorMobileNet:
    def __init__(self, model_path="checkpoints_affectnet_yolo/mobilenetv2_best.pth"):
        self.labels = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
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

    def predict(self, face_gray):
        if face_gray is None or face_gray.size == 0:
            return None, 0.0
        
        face_rgb = np.stack([face_gray] * 3, axis=-1)
        pil_img = Image.fromarray(face_rgb.astype('uint8'))
        img_tensor = self.transform(pil_img).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            logits = self.model(img_tensor)
            probs = F.softmax(logits, dim=1)[0]
        
        idx = torch.argmax(probs).item()
        conf = float(probs[idx])
        
        return self.labels[idx], conf
