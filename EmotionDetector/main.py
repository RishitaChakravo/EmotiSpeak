import cv2
from torchvision import transforms
import torch
from PIL import Image
from collections import deque
from collections import Counter
import threading

class_names = [
    "Surprise", "Fear", "Disgust",
    "Happy", "Sad", "Angry", "Neutral"
]


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

class VideoSession():
    def __init__(self, model):
        self._cap = None
        self._running = False
        self._thread = None
        self._emotion_log = []
        self._model = model

        self.face_detector = cv2.FaceDetectorYN.create(
            "face_detection_yunet_2023mar.onnx",
            "",
            (320, 320)
        )
            
        self.transform = transforms.Compose([
            transforms.Resize((224,224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485,0.456,0.406],
                std=[0.229,0.224,0.225]
            )
        ])

    def start(self):
        self._running = True
        self._cap = cv2.VideoCapture(0)
        self._cap.set(3, 640)
        self._cap.set(4, 480)
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._thread = threading.Thread(target= self._run)

    def _run(self):
        buffer = deque(maxlen=10)
        print("Video thread started")
        while self._running:
            success, img = self._cap.read()
            if not success:
                print("Camera failed")
                break

            img = cv2.resize(img, (640, 480))
            h, w, _ = img.shape

            self.face_detector.setInputSize((w, h))
            _, faces = self.face_detector.detect(img)

            if faces is not None:
                print(f"Faces detected: {len(faces)}")
                for face_data in faces:
                    x, y, fw, fh = map(int, face_data[:4])

                    pad = 20
                    x1 = max(0, x - pad)
                    y1 = max(0, y - pad)
                    x2 = min(w, x + fw + pad)
                    y2 = min(h, y + fh + pad)

                    face = img[y1:y2, x1:x2]
                    if face.size == 0 or face.shape[0] == 0 or face.shape[1] == 0:
                        print(f"Faces detected: {len(faces)}")
                        continue

                    face_resized = cv2.resize(face, (224, 224))
                    face_rgb = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
                    face_pil = Image.fromarray(face_rgb)
                    face_tensor = self.transform(face_pil).unsqueeze(0).to(self.device)

                    if face.shape != (1, 3, 224, 224):
                        print("Bad tensor shape:", face_tensor.shape)  
                        continue

                    with torch.no_grad():
                        output = self._model(face)

                    probs = torch.softmax(output, dim=1)
                    confidence, pred = torch.max(probs, dim=1)

                    emotion = class_names[pred]
                    self._emotion_log.append(emotion.lower())
                    print(f"Emotion detected: {emotion}")

                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(img, emotion, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                        print("No face detected in frame")
            cv2.imshow("Face", img)

            if cv2.waitKey(1) & 0xFF == 27:
                break
        print(f"Thread ending. Emotions logged: {self.emotion_log}")
    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join()
        if self._cap:
            self._cap.release()
        cv2.destroyAllWindows()
        return self._emotion_log

