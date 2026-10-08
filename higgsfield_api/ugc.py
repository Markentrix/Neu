"""UGC-Pipeline über die API: Host-Bild erzeugen, Sprecher-Clip mit deutschem
Text rendern. Ersetzt die Connector-Workflows (ugc-review-video) des Skills.

Schritte:
  1. create_host()   -> ein festes Host-Bild (SOUL V2, 9:16), wird als Referenz
                        gespeichert und in Serien nie neu erzeugt.
  2. talking_clip()  -> Clip mit nativem Ton: Seedance 2.0 reference-to-video
                        (Identität aus Referenzbild, optional eigene Tonspur per
                        audio_urls) oder Kling 3.0 image-to-video (sound on).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from .client import HiggsfieldClient
from .pricing import estimate_cost

HOST_LOOK = (
    "Realistic smartphone-style portrait of one adult person aged about 35, "
    "well-groomed, grounded and professional, plain navy or white or grey clothing "
    "without logos or text, no lanyard, no badge, no jewelry with text, calm direct look "
    "with a slight smile, natural daylight, bright tidy office with window light, soft "
    "neutral background without screens, brand logos, posters or signs, no text anywhere, "
    "no neon, no dark look, vertical framing, head and shoulders, looking at the camera"
)


def build_dialogue_prompt(script: str, scene: str, language: str = "Deutsch",
                          accent: str = "neutrales Hochdeutsch, leicht norddeutsch, kein Dialekt, kein englischer Akzent",
                          camera: str = "statische Smartphone-Aufnahme, Hochformat 9:16, Person spricht direkt in die Kamera") -> str:
    """Baut den Prompt so, dass das Modell den Text wörtlich als Dialog spricht."""
    script = " ".join(script.split())
    return (
        f"{scene}. {camera}. Eine erwachsene Person spricht ruhig, direkt, mit leichtem Lächeln. "
        f"Sprache: {language}, {accent}. Kein eingeblendeter Text, keine Schilder, keine Logos, "
        f"keine fremden Marken, kein Lanyard, kein Neon, helles natürliches Licht. "
        f"Die Person sagt wörtlich auf {language}: \"{script}\""
    )


def create_host(client: HiggsfieldClient, out_dir: str | Path = "output/host",
                look: str = HOST_LOOK, seed: Optional[int] = None,
                batch_size: int = 1) -> Dict[str, Any]:
    """Erzeugt das Host-Bild und legt es mit Metadaten ab."""
    params: Dict[str, Any] = {"prompt": look, "batch_size": batch_size}
    if seed is not None:
        params["seed"] = seed
    result = client.generate("soul2", out_dir=out_dir, **params)
    meta = {
        "request_id": result["request_id"],
        "files": result["files"],
        "urls": client.output_urls(result),
        "prompt": look,
        "seed": seed,
        "estimate": result["estimate"],
    }
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    (Path(out_dir) / "host-meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    return meta


def talking_clip(client: HiggsfieldClient, host_image_url: str, script: str, scene: str,
                 duration: int = 15, model: str = "seedance2-ref",
                 audio_url: Optional[str] = None, out_dir: str | Path = "output",
                 name: Optional[str] = None, dry_run: bool = False,
                 on_update=None) -> Dict[str, Any]:
    """Rendert einen Sprecher-Clip. host_image_url muss öffentlich erreichbar sein
    (Upload über client.upload() liefert eine passende URL)."""
    prompt = build_dialogue_prompt(script, scene)
    if model.startswith("seedance") and model.endswith("-ref"):
        params: Dict[str, Any] = {"prompt": prompt, "image_urls": [host_image_url],
                                  "duration": duration, "aspect_ratio": "9:16",
                                  "resolution": "1080p", "generate_audio": True}
        if audio_url:
            params["audio_urls"] = [audio_url]
    else:
        params = {"prompt": prompt, "image_url": host_image_url, "duration": duration}
    body = client.build_params(model, **params)
    est = estimate_cost(model, body)
    if dry_run:
        return {"model": model, "body": body, "estimate": est}
    job = client.submit(model, **body)
    result = client.wait(job["request_id"], on_update=on_update)
    files = client.download(result, out_dir, stem=name)
    return {"request_id": job["request_id"], "files": [str(f) for f in files],
            "urls": client.output_urls(result), "estimate": est, "prompt": prompt}
