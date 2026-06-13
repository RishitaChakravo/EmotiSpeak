import whisper
import re

SAMPLE_RATE = 16000  
CHANNELS = 1
 
FILLERS = [
    "you know", "i mean", "kind of", "sort of",
    "um", "uh", "er", "ah",
    "like", "basically", "actually", "literally",
    "so", "well", "okay", "right",
]

model = whisper.load_model("small") 


def transcribe_audio(audio_path: str) -> str:

        result = model.transcribe(
            audio_path,
            language="en",
            fp16=False,
            initial_prompt="Give raw text. Transcribe exactly as spoken, include all filler words like {um, uh, er, ah, like, you know} exactly as spoken. Do not clean up or remove any words.",
            condition_on_previous_text=False,
            no_speech_threshold=0.3,
            suppress_tokens=[]
        )
        
        return result["text"].strip()

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
    words = text.split()
    total_words = len(words)
    filler_data = detect_filler(text)
    non_filler_count = total_words - filler_data["total"]
 
    if duration_seconds <= 0 or non_filler_count <= 0:
        return 0.0
    return round((non_filler_count / duration_seconds) * 60, 1)

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
        "filler_percentage": round(filler_ratio * 100, 1)
    }
 
