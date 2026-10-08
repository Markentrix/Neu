"""Kleines Python-Modul für die Higgsfield-API (pay-as-you-go, ohne Abo).

Öffentliche Schnittstelle:
    from higgsfield_api import HiggsfieldClient, estimate_cost, MODELS
"""

from .client import HiggsfieldClient, HiggsfieldError
from .models import MODELS, ModelSpec
from .pricing import estimate_cost

__all__ = ["HiggsfieldClient", "HiggsfieldError", "MODELS", "ModelSpec", "estimate_cost"]
