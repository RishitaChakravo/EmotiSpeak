from fastapi import FastAPI, UploadFile, File, Form
import uvicorn
from test import transcribe_audio, analyze_speech
from fastapi.middleware.cors import CORSMiddleware
from model import model
import torch
from pyfile import VideoService, analyze_emotions
from fastapi.responses import StreamingResponse
import tempfile, os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://emoti-speak.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

vidService = VideoService(model=model)

@app.post("/api/audioops/start")
def start():

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

@app.post("/api/audio/upload")
async def getAudio(audio: UploadFile = File(...), duration: float = Form(...)):
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        content = await audio.read()
        tmp.write(content)

        tmp_path = tmp.name
    
    try:
        text = transcribe_audio(tmp_path)

        aud_data = analyze_speech(
            text, duration
        )

        return aud_data
    finally:
        os.remove(tmp_path)

@app.post("/api/audioops/stop")
def stop():
    try:
        vid_data = analyze_emotions(
            vidService.emotion_log
        )

        return {
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