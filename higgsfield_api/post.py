"""Nachbearbeitung mit ffmpeg: QA-Frames, Untertitel, Hook-Plate, Endcard.
Ersetzt den Sandbox-Schnitt der Connector-Workflows. Alles läuft lokal.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List, Optional


def _run(cmd: List[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True)


def probe(video: str | Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(video)],
        check=True, capture_output=True, text=True).stdout
    info = json.loads(out)
    streams = info.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), {})
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    return {"duration": float(info.get("format", {}).get("duration", 0)),
            "width": v.get("width"), "height": v.get("height"),
            "has_audio": a is not None}


def qa_frames(video: str | Path, out_dir: str | Path, every: float = 1.0) -> List[Path]:
    """Zieht alle `every` Sekunden ein Standbild für die Frozen-Frame-QA
    (Hände, Gesicht, Lippen, eingebackener Text). Claude kann die PNGs lesen."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    _run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vf", f"fps=1/{every}",
          str(out / "frame_%03d.png")])
    return sorted(out.glob("frame_*.png"))


def make_srt(script: str, duration: float, out_path: str | Path, max_words: int = 5) -> Path:
    """Verteilt das Skript gleichmäßig auf Untertitel-Blöcke. Danach gegen das
    finale Audio prüfen und Zeiten bei Bedarf von Hand anpassen."""
    words = script.split()
    blocks = [words[i:i + max_words] for i in range(0, len(words), max_words)]
    per = duration / max(len(blocks), 1)

    def ts(t: float) -> str:
        h, rem = divmod(t, 3600)
        m, s = divmod(rem, 60)
        return f"{int(h):02}:{int(m):02}:{int(s):02},{int((s % 1) * 1000):03}"

    lines = []
    for i, b in enumerate(blocks, 1):
        lines += [str(i), f"{ts((i - 1) * per)} --> {ts(i * per - 0.05)}", " ".join(b), ""]
    p = Path(out_path)
    p.write_text("\n".join(lines), encoding="utf-8")
    return p


def burn_subtitles(video: str | Path, srt: str | Path, out_path: str | Path,
                   font: str = "Inter", size: int = 17, bottom_frac: float = 0.19) -> Path:
    """Brennt Untertitel ein. bottom_frac = Abstand vom unteren Rand als Anteil der
    Höhe (9:16 Safe Area 330/1920 = 0,17). libass rechnet in 288 Einheiten Höhe."""
    margin_v = round(bottom_frac * 288)
    style = (f"FontName={font},FontSize={size},PrimaryColour=&H00FFFFFF,OutlineColour=&H00201A0B,"
             f"BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV={margin_v},MarginL=20,MarginR=20")
    srt_path = str(srt).replace("\\", "/").replace(":", "\\:")
    _run(["ffmpeg", "-y", "-v", "error", "-i", str(video),
          "-vf", f"subtitles='{srt_path}':force_style='{style}'",
          "-c:a", "copy", str(out_path)])
    return Path(out_path)


def overlay_png(video: str | Path, png: str | Path, out_path: str | Path,
                start: float = 0.0, end: float = 3.0, x: str = "(W-w)/2", y: str = "0.14*H",
                fit_width: bool = True) -> Path:
    """Legt ein PNG (z.B. Hook-Plate, KI-Icon) für ein Zeitfenster über das Video.
    y darf Ausdrücke mit H (Videohöhe) enthalten; fit_width skaliert das PNG auf Videobreite."""
    pre = "[1:v][0:v]scale2ref=w=iw:h=ow/mdar[ov][base];[base][ov]" if fit_width else "[0:v][1:v]"
    _run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-i", str(png),
          "-filter_complex", f"{pre}overlay={x}:{y}:enable='between(t,{start},{end})'",
          "-c:a", "copy", str(out_path)])
    return Path(out_path)


def loudnorm(video: str | Path, out_path: str | Path, target_i: float = -16.0, tp: float = -1.5) -> Path:
    """Einheitliche Lautheit (EBU R128), Ziel -16 LUFS für Social."""
    _run(["ffmpeg", "-y", "-v", "error", "-i", str(video),
          "-af", f"loudnorm=I={target_i}:TP={tp}:LRA=11", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
          str(out_path)])
    return Path(out_path)


def append_endcard(video: str | Path, endcard_png: str | Path, out_path: str | Path,
                   seconds: float = 2.5, fade: float = 0.5) -> Path:
    """Hängt die Endcard (1080x1920 PNG) an; Ton läuft aus."""
    info = probe(video)
    w, h = info["width"], info["height"]
    audio_in = ["-f", "lavfi", "-t", str(seconds), "-i", "anullsrc=r=48000:cl=stereo"]
    fc = (f"[1:v]scale={w}:{h},format=yuv420p,loop=loop=-1:size=1:start=0,"
          f"trim=duration={seconds},setpts=PTS-STARTPTS[ec];"
          f"[0:a]afade=t=out:st={max(info['duration'] - fade, 0)}:d={fade}[a0];"
          f"[0:v][a0][ec][2:a]concat=n=2:v=1:a=1[v][a]")
    _run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-i", str(endcard_png), *audio_in,
          "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
          "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(out_path)])
    return Path(out_path)


def concat(videos: List[str | Path], out_path: str | Path) -> Path:
    """Fügt mehrere Clips gleicher Größe aneinander (z.B. 2 Clips für 30 s)."""
    n = len(videos)
    inputs = []
    for v in videos:
        inputs += ["-i", str(v)]
    fc = "".join(f"[{i}:v][{i}:a]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]"
    _run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", fc,
          "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p",
          "-c:a", "aac", str(out_path)])
    return Path(out_path)


def transcribe(video: str | Path, language: str = "de", model_size: str = "base") -> List[dict]:
    """Transkribiert die Tonspur lokal (faster-whisper) für das Aussprache-Gate.
    Gibt Segmente mit start, end, text zurück. Benötigt `pip install faster-whisper`."""
    import tempfile
    import wave
    try:
        import numpy as np
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("faster-whisper fehlt: pip install faster-whisper") from exc
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "audio.wav"
        _run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000", str(wav)])
        with wave.open(str(wav)) as w:
            audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    segs, _info = WhisperModel(model_size, device="cpu", compute_type="int8").transcribe(audio, language=language)
    return [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]
