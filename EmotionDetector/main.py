import cv2
from torchvision import transforms
import torch
from model import model
from PIL import Image
from collections import deque
from collections import Counter

face_detector = cv2.FaceDetectorYN.create(
    "face_detection_yunet_2023mar.onnx",
    "",
    (320, 320)
)

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

transform = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485,0.456,0.406],
        std=[0.229,0.224,0.225]
    )
])

class_names = [
    "Surprise", "Fear", "Disgust",
    "Happy", "Sad", "Angry", "Neutral"
]

emotion_log = []

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

buffer = deque(maxlen=10)

while True:
    success, img = cap.read()
    if not success:
        break

    img = cv2.resize(img, (640, 480))
    h, w, _ = img.shape

    face_detector.setInputSize((w, h))
    _, faces = face_detector.detect(img)

    if faces is not None:
        for face_data in faces:
            x, y, fw, fh = map(int, face_data[:4])

            pad = 20
            x1 = max(0, x - pad)
            y1 = max(0, y - pad)
            x2 = min(w, x + fw + pad)
            y2 = min(h, y + fh + pad)

            face = img[y1:y2, x1:x2]

            if face.size == 0:
                continue

            face = cv2.resize(face, (224,224))
            face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
            face = Image.fromarray(face)
            face = transform(face).unsqueeze(0).to(device)

            with torch.no_grad():
                output = model(face)

            probs = torch.softmax(output, dim=1)
            confidence, pred = torch.max(probs, dim=1)

            emotion = class_names[pred]
            emotion_log.append(emotion.lower())

            cv2.rectangle(img, (x1, y1), (x2, y2), (0,255,0), 2)
            cv2.putText(img, emotion, (x1, y1-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    cv2.imshow("Face", img)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()

POSITIVE_EMOTIONS = {'happy', 'surprise'}
NEGATIVE_EMOTIONS = {'fear', 'disgust', 'anger', 'sad'}
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
        "dominant_emotion" : counts.most_common(1),
        "positive_ratio" : round(positive / total, 2),
        "negative_ratio" : round(negative / total, 2),
        "neutral_ratio" : round(neutral / total, 2),
        "confidence_level" : interpret_confidence(positive, negative, total),
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