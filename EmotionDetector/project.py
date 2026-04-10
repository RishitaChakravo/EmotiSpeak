from fastapi import FastAPI
import uvicorn
from test import RecordingSession, transcribe_audio, analyze_speech
from fastapi.middleware.cors import CORSMiddleware
from model import model
import torch
from main import VideoSession, analyze_emotions
from fastapi.responses import StreamingResponse

def generate_frames(vid_session: VideoSession):
    while vid_session._running:
        frame = vid_session.get_frame()
        if frame is None:
            continue
        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
        )

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
vidSession = VideoSession(model=model)
@app.get('/api/video/stream')
def video_stream():
    return StreamingResponse(
        generate_frames(vidSession),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )

@app.post('/api/audioops/start')
def start():
    vidSession.start()
    session.start()
    return {"status": "Audio and Video Recording", "loading" : False}

@app.post('/api/audioops/stop')
def stop():
    try:
        audio, duration = session.stop()
        emotion_log = vidSession.stop()
        
        text = transcribe_audio(audio)
        
        vid_data = analyze_emotions(emotion_log)
        aud_data = analyze_speech(text, duration)
        return {
            "audio" : aud_data,
            "video" : vid_data,
            "loading": False
        }
    except Exception as e:
        print("ERROR:", e)
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)