from fastapi import FastAPI, UploadFile, File
import uvicorn
from test import RecordingSession, transcribe_audio, analyze_speech
from fastapi.middleware.cors import CORSMiddleware
from model import model
import torch
from pyfile import VideoService, analyze_emotions
from fastapi.responses import StreamingResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

session = RecordingSession()
vidService = VideoService(model=model)

@app.post("/api/audioops/start")
def start():

    session.start()

    vidService.reset()
    return {
        "status": "Recording Started",
        "loading": False
    }

@app.post("/api/video/frame")
async def process_frame(
    file: UploadFile = File(...)
):
    image_bytes = await file.read()

    return vidService.process_frame(
        image_bytes
    )

@app.post("/api/audioops/stop")
def stop():
    try:
        audio, duration = session.stop()
        text = transcribe_audio(audio)
        vid_data = analyze_emotions(
            vidService.emotion_log
        )
        aud_data = analyze_speech(
            text,
            duration
        )
        return {
            "audio": aud_data,
            "video": vid_data,
            "loading": False
        }

    except Exception as e:
        print("ERROR:", e)

        return {
            "error": str(e)
        }

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)