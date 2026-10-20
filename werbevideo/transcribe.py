"""Aussprache-QA: Transkription (faster-whisper base, de) mit Wortzeiten."""
import subprocess, sys
import numpy as np
from faster_whisper import WhisperModel
m = WhisperModel("base", device="cpu", compute_type="int8")
for p in sys.argv[1:]:
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-f", "s16le", "-ar", "16000", "-ac", "1", "-"], capture_output=True, check=True).stdout
    audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
    segs, _ = m.transcribe(audio, language="de", word_timestamps=True)
    words = [w for s in segs for w in s.words]
    print(p, "\n ", " ".join(w.word.strip() for w in words))
    print("  ", " ".join(f"{w.word.strip()}@{w.start:.2f}" for w in words))
