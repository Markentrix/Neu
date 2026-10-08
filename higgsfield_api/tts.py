"""Sprachspur über ElevenLabs (Text zu Sprache), als Audio-Referenz für Seedance.

Zugang: Network Secret für api.elevenlabs.io mit Header `xi-api-key` (kein Präfix),
in der Cloud-Umgebung hängt der Proxy ihn an. Lokal: Umgebungsvariable ELEVENLABS_API_KEY.
Kosten fallen bei ElevenLabs pro Zeichen an, ein 25-s-Skript hat etwa 300 Zeichen.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

BASE = "https://api.elevenlabs.io/v1"
DEFAULT_MODEL = "eleven_multilingual_v2"


def _headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    h = {"Accept": "application/json"}
    key = os.getenv("ELEVENLABS_API_KEY")
    if key:
        h["xi-api-key"] = key
    if extra:
        h.update(extra)
    return h


def check() -> Dict[str, Any]:
    r = requests.get(f"{BASE}/user/subscription", headers=_headers(), timeout=30)
    r.raise_for_status()
    d = r.json()
    return {"tier": d.get("tier"), "character_count": d.get("character_count"),
            "character_limit": d.get("character_limit")}


def list_voices(language: Optional[str] = "de", gender: Optional[str] = None) -> List[Dict[str, Any]]:
    """Eigene und Standard-Stimmen; Filter nach Sprache/Geschlecht aus den Labels (lose)."""
    r = requests.get(f"{BASE}/voices", headers=_headers(), timeout=30)
    r.raise_for_status()
    out = []
    for v in r.json().get("voices", []):
        labels = {k: str(val).lower() for k, val in (v.get("labels") or {}).items()}
        langs = {labels.get("language", ""), *(vl.get("language", "").lower() for vl in v.get("verified_languages") or [])}
        if language and language not in " ".join(langs) and "multilingual" not in labels.get("use_case", ""):
            pass  # Standardstimmen sind mehrsprachig; Sprache ist nur ein Hinweis
        if gender and labels.get("gender") != gender:
            continue
        out.append({"voice_id": v["voice_id"], "name": v.get("name"), "labels": labels,
                    "preview_url": v.get("preview_url")})
    return out


def synthesize(text: str, voice_id: str, out_path: str | Path, model_id: str = DEFAULT_MODEL,
               stability: float = 0.5, similarity: float = 0.8, style: float = 0.15,
               speed: float = 1.0, output_format: str = "mp3_44100_128",
               language_code: Optional[str] = "de") -> Path:
    """Erzeugt die Sprachspur. output_format mp3_44100_128 (Standard) oder pcm_44100 (WAV-Rohdaten)."""
    body: Dict[str, Any] = {
        "text": text, "model_id": model_id,
        "voice_settings": {"stability": stability, "similarity_boost": similarity,
                           "style": style, "use_speaker_boost": True, "speed": speed},
    }
    if language_code and model_id != "eleven_multilingual_v2":
        body["language_code"] = language_code
    r = requests.post(f"{BASE}/text-to-speech/{voice_id}", params={"output_format": output_format},
                      headers=_headers({"Content-Type": "application/json", "Accept": "audio/mpeg"}),
                      json=body, timeout=120)
    if not r.ok:
        raise RuntimeError(f"ElevenLabs HTTP {r.status_code}: {r.text[:300]}")
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(r.content)
    return out


def to_wav(src: str | Path, out_path: str | Path, loudness: float = -16.0) -> Path:
    """MP3 zu WAV 48 kHz mono mit normierter Lautheit (für Upload und Lippensync)."""
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-ac", "1", "-ar", "48000",
                    "-af", f"loudnorm=I={loudness}:TP=-1.5:LRA=11", str(out_path)], check=True)
    return Path(out_path)
