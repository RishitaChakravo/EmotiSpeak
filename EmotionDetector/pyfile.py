import cv2
from torchvision import transforms
import torch
from PIL import Image
from collections import deque
from collections import Counter
import threading
import numpy as np
class_names = [
    "Surprise", "Fear", "Disgust",
    "Happy", "Sad", "Angry", "Neutral"
]

POSITIVE_EMOTIONS = {'happy', 'surprise'}
NEGATIVE_EMOTIONS = {'fear', 'disgust', 'angry', 'sad'}
NEUTRAL_EMOTIONS = {'neutral'}

def analyze_emotions(emotion_log) -> dict:
    if not emotion_log:
        return {"error": "No emotions recorded"}
    total = len(emotion_log)
    counts = Counter(emotion_log)

    positive = sum(counts.get(e, 0) for e in POSITIVE_EMOTIONS)
    negative = sum(counts.get(e, 0) for e in NEGATIVE_EMOTIONS)
    neutral = sum(counts.get(e, 0) for e in NEUTRAL_EMOTIONS)

    return {
        "dominant_emotion": counts.most_common(1),
        "positive_ratio": round(positive / total, 2),
        "negative_ratio": round(negative / total, 2),
        "neutral_ratio": round(neutral / total, 2),
        "confidence_level": interpret_confidence(positive, negative, total),
    }

def interpret_confidence(positive, negative, total) -> str:
    pos_ratio = positive / total
    neg_ratio = negative / total
    if pos_ratio > 0.5:
        return "Confident and engaged"
    elif neg_ratio > 0.4:
        return "Nervous or stressed"
    elif neg_ratio > 0.2 and pos_ratio > 0.3:
        return "Moderate confidence"
    else:
        return "Neutral and composed"

class VideoService:
    def __init__(self, model):
        self.model = model

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.model.to(self.device)
        self.model.eval()

        self.emotion_log = []

        self.face_detector = cv2.FaceDetectorYN.create(
            "face_detection_yunet_2023mar.onnx",
            "",
            (320, 320)
        )

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])

    def process_frame(self, image_bytes):

        nparr = np.frombuffer(image_bytes, np.uint8)

        img = cv2.imdecode(
            nparr,
            cv2.IMREAD_COLOR
        )

        if img is None:
            return {"error": "Invalid image"}

        h, w, _ = img.shape

        self.face_detector.setInputSize((w, h))

        _, faces = self.face_detector.detect(img)

        if faces is None:
            return {"emotion": None}

        face_data = faces[0]

        x, y, fw, fh = map(int, face_data[:4])

        pad = 20

        x1 = max(0, x - pad)
        y1 = max(0, y - pad)

        x2 = min(w, x + fw + pad)
        y2 = min(h, y + fh + pad)

        face = img[y1:y2, x1:x2]

        if face.size == 0:
            return {"emotion": None}

        face_resized = cv2.resize(face, (224, 224))

        face_rgb = cv2.cvtColor(
            face_resized,
            cv2.COLOR_BGR2RGB
        )

        face_pil = Image.fromarray(face_rgb)

        face_tensor = (
            self.transform(face_pil)
            .unsqueeze(0)
            .to(self.device)
        )

        with torch.no_grad():
            output = self.model(face_tensor)

        probs = torch.softmax(output, dim=1)

        confidence, pred = torch.max(
            probs,
            dim=1
        )

        emotion = class_names[pred.item()]

        self.emotion_log.append(
            emotion.lower()
        )

        return {
            "emotion": emotion,
            "confidence": float(confidence.item())
        }

    def reset(self):
        self.emotion_log = []