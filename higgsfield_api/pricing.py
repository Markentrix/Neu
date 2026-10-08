"""Kostenschätzung vor dem Absenden.

Die API hat keinen dokumentierten Estimate-Endpunkt. Wir rechnen deshalb lokal
mit den Listenpreisen aus models.py. Fehlgeschlagene oder als NSFW markierte
Jobs werden laut Higgsfield nicht berechnet.
"""

from typing import Dict, Any
from .models import ModelSpec, get_model


def estimate_cost(model: "ModelSpec | str", params: Dict[str, Any]) -> Dict[str, Any]:
    spec = get_model(model) if isinstance(model, str) else model
    merged = {**spec.defaults, **params}
    if spec.unit == "second":
        units = int(merged.get("duration", spec.defaults.get("duration", 0)))
    else:
        units = int(merged.get("num_images", 1))
    list_total = round(units * spec.list_price_usd, 4)
    return {
        "model": spec.key,
        "path": spec.path,
        "units": units,
        "unit": spec.unit,
        "list_price_per_unit_usd": spec.list_price_usd,
        "list_total_usd": list_total,
        "note": "Listenpreis als Obergrenze; Kontorabatte senken den Betrag. "
                "Verbindlich ist die Abrechnung in console.higgsfield.ai.",
    }


def format_estimate(est: Dict[str, Any]) -> str:
    return (f"{est['model']}: {est['units']} {est['unit']}(s) x "
            f"{est['list_price_per_unit_usd']:.4f} USD = max. {est['list_total_usd']:.4f} USD")
