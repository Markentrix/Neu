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
    duration_options: Optional[tuple] = None


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
    # --- Bild ------------------------------------------------------------
    "soul": ModelSpec(
        key="soul",
        path="/higgsfield-ai/soul/standard",
        kind="image", unit="image", list_price_usd=0.0938,
        description="Higgsfield SOUL Standard, Text zu Bild, 2K oder 4K",
        defaults={"num_images": 1, "resolution": "2K", "aspect_ratio": "4:3"},
        required=("prompt",),
    ),
}


def get_model(key: str) -> ModelSpec:
    try:
        return MODELS[key]
    except KeyError:
        known = ", ".join(sorted(MODELS))
        raise KeyError(f"Unbekanntes Modell '{key}'. Bekannt: {known}") from None
