from fastapi import FastAPI
import uvicorn
from test import RecordingSession, transcribe_audio, analyze_speech
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session = RecordingSession()

@app.post('/api/audioops/start')
def start():
    session.start()
    return {"status": "recording"}

@app.post('/api/audioops/stop')
def stop():
    try:
        audio, duration = session.stop()
        text = transcribe_audio(audio)
        return analyze_speech(text, duration)
    except Exception as e:
        print("ERROR:", e)
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)