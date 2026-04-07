import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import tempfile
import re
import time

SAMPLE_RATE = 16000  
CHANNELS = 1
 
FILLERS = [
    "you know", "i mean", "kind of", "sort of",
    "um", "uh", "er", "ah",
    "like", "basically", "actually", "literally",
    "so", "well", "okay", "right",
]

model = whisper.load_model("base")

def record_audio(duration: float) -> np.ndarray:
    audio = sd.rec(
        int(duration * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
    )
    sd.wait()
    return audio

def transcribe_audio(audio: np.ndarray) -> str:
    import os

    tmp_path = "C:/Users/RISHITA CHAKRAVORTY/OneDrive/Desktop/App/temp_audio.wav"
    
    try:
        audio = audio.flatten()
 
        if audio.max() > 1.0 or audio.min() < -1.0:
            audio = audio / np.max(np.abs(audio))
        
        wav.write(tmp_path, SAMPLE_RATE, audio)
        result = model.transcribe(tmp_path)
        return result["text"].strip()
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def detect_filler(text: str) -> dict:
    text_lower = text.lower()
    counts = {}
    for filler in FILLERS:
        pattern = r"\b" + re.escape(filler) + r"\b"
        matches = re.findall(pattern, text_lower)
        if matches:
            counts[filler] = len(matches)
    return {
        "counts": counts,
        "total": sum(counts.values()),
    }

def calculate_wpm(text: str, duration_seconds: float) -> float:
    """
    Calculate words per minute.
    `duration_seconds` is the actual recorded/elapsed time.
    """
    word_count = len(text.split())
    if duration_seconds <= 0 or word_count == 0:
        return 0.0
    return round((word_count / duration_seconds) * 60, 1)

def analyze_speech(text: str, duration_seconds: float) -> dict:
    words = text.split()
    word_count = len(words)
    filler_data = detect_filler(text)
    filler_ratio = round(filler_data["total"] / word_count, 3) if word_count > 0 else 0.0
 
    return {
        "transcript": text,
        "word_count": word_count,
        "wpm": calculate_wpm(text, duration_seconds),
        "fillers": filler_data,
        "filler_ratio": filler_ratio,
    }
 
class RecordingSession:
    def __init__(self):
        self._start_time = None
        self._audio_chunks = []
        self._stream = None
 
    def start(self):
        self._start_time = time.time()
        self._audio_chunks = []
 
        def callback(indata, frames, time_info, status):
            self._audio_chunks.append(indata.copy())
 
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            callback=callback,
        )
        self._stream.start()
 
    def stop(self) -> tuple[np.ndarray, float]:
        if self._stream is None:
            raise RuntimeError("Session was never started.")
        self._stream.stop()
        self._stream.close()
        duration = time.time() - self._start_time
        audio = np.concatenate(self._audio_chunks, axis=0) if self._audio_chunks else np.array([])
        return audio, duration
 