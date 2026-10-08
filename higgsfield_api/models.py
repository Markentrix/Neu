"""Registry der Modelle, die wir über die Higgsfield-API ansprechen.

Pfade und Parameter stammen aus https://docs.higgsfield.ai/docs/openapi.json.
Preise sind Listenpreise in US-Dollar von https://higgsfield.ai/higgsfield-api
(Stand Oktober 2026). Das eigene Konto hat meist einen Rabatt von 15 bis 50
Prozent, die Schätzung ist also eine Obergrenze. Verbindlich ist nur die
Abrechnung in der Konsole: https://console.higgsfield.ai
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass(frozen=True)
class ModelSpec:
    key: str                      # unser Kurzname, z.B. "hailuo-t2v"
    path: str                     # API-Pfad nach https://api.higgsfield.ai
    kind: str                     # "video" oder "image"
    unit: str                     # "second" oder "image"
    list_price_usd: float         # Listenpreis pro Einheit
    description: str
    defaults: Dict[str, Any] = field(default_factory=dict)
    required: tuple = ()
    duration_options: Optional[tuple] = None   # feste Werte, z.B. (5, 10)
    duration_range: Optional[tuple] = None     # (min, max) in Sekunden
    required_any: tuple = ()                   # mindestens eines dieser Felder


MODELS: Dict[str, ModelSpec] = {
    # --- Video, günstig, für Tests und einfache Clips --------------------
    "hailuo-t2v": ModelSpec(
        key="hailuo-t2v",
        path="/minimax/hailuo-2.3/standard/text-to-video",
        kind="video", unit="second", list_price_usd=0.0467,
        description="MiniMax Hailuo 2.3, Text zu Video, 6 oder 10 s",
        defaults={"duration": 6, "prompt_optimizer": True},
        required=("prompt",), duration_options=(6, 10),
    ),
    "hailuo-i2v": ModelSpec(
        key="hailuo-i2v",
        path="/minimax/hailuo-2.3/standard/image-to-video",
        kind="video", unit="second", list_price_usd=0.0467,
        description="MiniMax Hailuo 2.3, Bild zu Video, 6 oder 10 s",
        defaults={"duration": 6, "prompt_optimizer": True},
        required=("prompt", "image_url"), duration_options=(6, 10),
    ),
    # --- Video, Kling 2.5 Turbo -------------------------------------------
    "kling-std-i2v": ModelSpec(
        key="kling-std-i2v",
        path="/kling-video/v2.5-turbo/standard/image-to-video",
        kind="video", unit="second", list_price_usd=0.042,
        description="Kling 2.5 Turbo Standard, Bild zu Video, 5 oder 10 s",
        defaults={"duration": 5, "cfg_scale": 0.5, "negative_prompt": ""},
        required=("prompt", "image_url"), duration_options=(5, 10),
    ),
    "kling-pro-i2v": ModelSpec(
        key="kling-pro-i2v",
        path="/kling-video/v2.5-turbo/pro/image-to-video",
        kind="video", unit="second", list_price_usd=0.042,
        description="Kling 2.5 Turbo Pro, Bild zu Video, 5 oder 10 s",
        defaults={"duration": 5, "cfg_scale": 0.5, "negative_prompt": ""},
        required=("prompt", "image_url"), duration_options=(5, 10),
    ),
    "kling-pro-t2v": ModelSpec(
        key="kling-pro-t2v",
        path="/kling-video/v2.5-turbo/pro/text-to-video",
        kind="video", unit="second", list_price_usd=0.042,
        description="Kling 2.5 Turbo Pro, Text zu Video, 5 oder 10 s",
        defaults={"duration": 5, "cfg_scale": 0.5, "negative_prompt": ""},
        required=("prompt",), duration_options=(5, 10),
    ),
    # --- Video mit nativem Ton, Sprecher-Clips (UGC) ---------------------
    "seedance2-ref": ModelSpec(
        key="seedance2-ref",
        path="/bytedance/seedance-2.0/reference-to-video",
        kind="video", unit="second", list_price_usd=0.1407,
        description="Seedance 2.0, Referenzbilder (Host) + optional Audio zu Video mit Ton, 4-15 s",
        defaults={"duration": 5, "resolution": "1080p", "aspect_ratio": "9:16", "generate_audio": True},
        required=(), required_any=("image_urls", "video_urls"), duration_range=(4, 15),
    ),
    "seedance2-i2v": ModelSpec(
        key="seedance2-i2v",
        path="/bytedance/seedance-2.0/image-to-video",
        kind="video", unit="second", list_price_usd=0.1407,
        description="Seedance 2.0, Startbild zu Video mit Ton, 4-15 s (Format folgt dem Bild)",
        defaults={"duration": 5, "resolution": "1080p", "generate_audio": True},
        required=("image_url",), duration_range=(4, 15),
    ),
    "seedance25-ref": ModelSpec(
        key="seedance25-ref",
        path="/bytedance/seedance-2.5/reference-to-video",
        kind="video", unit="second", list_price_usd=0.2057,
        description="Seedance 2.5, Referenzbilder + optional Audio zu Video mit Ton, 4-30 s",
        defaults={"duration": 5, "resolution": "1080p", "aspect_ratio": "9:16", "generate_audio": True},
        required=(), required_any=("image_urls", "video_urls"), duration_range=(4, 30),
    ),
    "seedance25-t2v": ModelSpec(
        key="seedance25-t2v",
        path="/bytedance/seedance-2.5/text-to-video",
        kind="video", unit="second", list_price_usd=0.2057,
        description="Seedance 2.5, Text zu Video mit Ton, 4-30 s, Host wird im Prompt beschrieben",
        defaults={"duration": 5, "resolution": "1080p", "aspect_ratio": "9:16", "generate_audio": True},
        required=("prompt",), duration_range=(4, 30),
    ),
    "seedance25-i2v": ModelSpec(
        key="seedance25-i2v",
        path="/bytedance/seedance-2.5/image-to-video",
        kind="video", unit="second", list_price_usd=0.2057,
        description="Seedance 2.5, Startbild zu Video mit Ton, 4-30 s (Format folgt dem Bild)",
        defaults={"duration": 5, "resolution": "1080p", "generate_audio": True},
        required=("image_url",), duration_range=(4, 30),
    ),
    "kling3-std-i2v": ModelSpec(
        key="kling3-std-i2v",
        path="/kling-video/v3.0/std/image-to-video",
        kind="video", unit="second", list_price_usd=0.084,
        description="Kling 3.0 Standard, Startbild zu Video mit nativem Ton, 3-15 s",
        defaults={"duration": 5, "sound": "on", "cfg_scale": 0.5},
        required=("prompt", "image_url"), duration_range=(3, 15),
    ),
    "kling3-pro-i2v": ModelSpec(
        key="kling3-pro-i2v",
        path="/kling-video/v3.0/pro/image-to-video",
        kind="video", unit="second", list_price_usd=0.084,
        description="Kling 3.0 Pro, Startbild zu Video mit nativem Ton, 3-15 s",
        defaults={"duration": 5, "sound": "on", "cfg_scale": 0.5},
        required=("prompt", "image_url"), duration_range=(3, 15),
    ),
    # --- Bild ------------------------------------------------------------
    "soul2": ModelSpec(
        key="soul2",
        path="/higgsfield-ai/soul/v2/standard",
        kind="image", unit="image", list_price_usd=0.0032,
        description="Higgsfield SOUL V2, Portrait/Editorial, 720p oder 1080p, Host-Referenz",
        defaults={"aspect_ratio": "9:16", "resolution": "1080p", "enhance_prompt": False, "batch_size": 1},
        required=("prompt",),
    ),
    "soul": ModelSpec(
        key="soul",
        path="/higgsfield-ai/soul/standard",
        kind="image", unit="image", list_price_usd=0.0938,
        description="Higgsfield SOUL Standard, Text zu Bild, 720p oder 1080p",
        defaults={"num_images": 1, "resolution": "1080p", "aspect_ratio": "4:3"},
        required=("prompt",),
    ),
}


def get_model(key: str) -> ModelSpec:
    try:
        return MODELS[key]
    except KeyError:
        known = ", ".join(sorted(MODELS))
        raise KeyError(f"Unbekanntes Modell '{key}'. Bekannt: {known}") from None
