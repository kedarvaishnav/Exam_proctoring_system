import os
import sys
import json
import time
import sounddevice as sd
import numpy as np
import wavio
from scipy.io import wavfile
import shutil
import warnings

_builtin_print = print
def print(*args, **kwargs):
    if kwargs.pop("json_stdout", False):
        _builtin_print(*args, **kwargs)
    else:
        _builtin_print(*args, file=sys.stderr, **kwargs)
warnings.simplefilter("always")
def warn_to_stderr(message, category, filename, lineno, file=None, line=None):
    print(f"{filename}:{lineno}: {category.__name__}: {message}", file=sys.stderr)
warnings.showwarning = warn_to_stderr

try:
    import whisper
    HAVE_WHISPER = True
except:
    HAVE_WHISPER = False

try:
    from pyannote.audio import Pipeline
    HAVE_DIARIZATION = True
except:
    HAVE_DIARIZATION = False

CHUNK_DURATION = 3
SR = 16000
APPLY_AUTOGAIN = True
TARGET_RMS = 0.1
MAX_GAIN = 20.0
CHEATING_KEYWORDS = ["answer", "option", "solve", "google", "tell me", "what is"]

def record_chunk(duration=CHUNK_DURATION, sr=SR):
    audio = sd.rec(int(duration*sr), samplerate=sr, channels=1, dtype="float32")
    sd.wait()
    audio = audio.flatten()
    rms = float(np.sqrt(np.mean(audio**2)))
    if APPLY_AUTOGAIN and 0 < rms < TARGET_RMS/5:
        gain = min(MAX_GAIN, TARGET_RMS / rms)
        audio = np.clip(audio * gain, -1.0, 1.0)
        rms = float(np.sqrt(np.mean(audio**2)))
    return audio, rms

def save_wav(audio, sr, path="temp.wav"):
    path = os.path.abspath(path)
    try:
        wavio.write(path, audio, sr, sampwidth=2)
    except:
        ai16 = np.int16(np.clip(audio, -1, 1)*32767)
        wavfile.write(path, sr, ai16)
    return path

def load_diarization_pipeline():
    if not HAVE_DIARIZATION:
        return None
    try:
        return Pipeline.from_pretrained("pyannote/speaker-diarization")
    except:
        return None

def diarize(pipeline, wav_path):
    if pipeline is None:
        return 1, []
    diarization = pipeline(wav_path)
    speakers = set()
    segments = []
    for segment, _, label in diarization.itertracks(yield_label=True):
        speakers.add(label)
        segments.append((float(segment.start), float(segment.end), label))
    return len(speakers), segments

def transcribe_whisper_file(path):
    if not HAVE_WHISPER:
        return ""
    try:
        model = whisper.load_model("base")
        result = model.transcribe(path)
        return result.get("text", "").strip()
    except:
        return ""

def has_cheating_keywords(text):
    low = text.lower()
    return any(k in low for k in CHEATING_KEYWORDS)

def main():
    diarization_pipeline = load_diarization_pipeline()
    while True:
        try:
            audio, rms = record_chunk()
            wav_path = save_wav(audio, SR, "temp.wav")
            n_speakers, segments = diarize(diarization_pipeline, wav_path)
            text = transcribe_whisper_file(wav_path)
            cheating_detected = has_cheating_keywords(text) or rms > TARGET_RMS
            output = {
                "rms": round(rms, 4),
                "speakers": n_speakers,
                "segments": segments,
                "transcription": text,
                "cheating_detected": cheating_detected
            }
            print(json.dumps(output), flush=True, json_stdout=True)
            if os.path.exists(wav_path):
                os.remove(wav_path)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True, json_stdout=True)
            time.sleep(1)

if __name__ == "__main__":
    main()
