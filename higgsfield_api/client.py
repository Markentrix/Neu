"""HTTP-Client für die Higgsfield-API.

Authentifizierung:
  * In der Claude-Cloud-Umgebung hängt der Agent-Proxy den Header
    "Authorization: Key ID:SECRET" selbst an (Network secret für
    api.higgsfield.ai). Dann muss hier nichts gesetzt werden.
  * Lokal: Umgebungsvariable HF_KEY="ID:SECRET" oder HF_API_KEY und
    HF_API_SECRET setzen. Niemals den Schlüssel ins Repo schreiben.

Ablauf: submit() -> request_id -> wait() pollt den Status -> download().
"""

from __future__ import annotations

import mimetypes
import os
import random
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import requests

from .models import ModelSpec, get_model
from .pricing import estimate_cost

BASE_URL = "https://api.higgsfield.ai"
TERMINAL = {"completed", "failed", "nsfw", "canceled", "cancelled"}


class HiggsfieldError(RuntimeError):
    def __init__(self, message: str, status_code: Optional[int] = None,
                 correlation_id: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.correlation_id = correlation_id


def _credentials_from_env() -> Optional[str]:
    key = os.getenv("HF_KEY")
    if key:
        return key
    kid, sec = os.getenv("HF_API_KEY"), os.getenv("HF_API_SECRET")
    if kid and sec:
        return f"{kid}:{sec}"
    return None


class HiggsfieldClient:
    def __init__(self, base_url: str = BASE_URL, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers["Accept"] = "application/json"
        creds = _credentials_from_env()
        if creds:
            self.session.headers["Authorization"] = f"Key {creds}"
        # Ohne Umgebungsvariablen verlassen wir uns auf den Proxy der Cloud-Umgebung.

    # ------------------------------------------------------------ HTTP
    def _request(self, method: str, url: str, retries: int = 3, **kw) -> requests.Response:
        if not url.startswith("http"):
            url = f"{self.base_url}{url}"
        delay = 1.0
        last_exc: Optional[Exception] = None
        for attempt in range(retries + 1):
            try:
                resp = self.session.request(method, url, timeout=self.timeout, **kw)
            except requests.RequestException as exc:
                last_exc = exc
            else:
                if resp.status_code < 500:
                    return resp
                last_exc = HiggsfieldError(f"HTTP {resp.status_code}: {resp.text[:300]}",
                                           resp.status_code, resp.headers.get("X-Correlation-ID"))
            if attempt < retries:
                time.sleep(delay + random.random() * 0.5)
                delay = min(delay * 2, 8)
        raise HiggsfieldError(f"Anfrage fehlgeschlagen: {last_exc}")

    @staticmethod
    def _raise_for_error(resp: requests.Response) -> Dict[str, Any]:
        cid = resp.headers.get("X-Correlation-ID")
        try:
            body = resp.json()
        except ValueError:
            body = {"detail": resp.text[:300]}
        if resp.ok:
            return body
        detail = body.get("detail", body) if isinstance(body, dict) else body
        hints = {
            401: "Ungültige oder fehlende API-Zugangsdaten.",
            403: "Guthaben reicht nicht. In console.higgsfield.ai aufladen.",
            404: "Modell oder Request-ID für dieses Konto nicht gefunden.",
            422: "Parameter ungültig.",
            423: "Modell vorübergehend gesperrt, später erneut versuchen.",
            503: "Modell nicht bereit, später erneut versuchen.",
        }
        hint = hints.get(resp.status_code, "")
        raise HiggsfieldError(f"HTTP {resp.status_code} {hint} Detail: {detail}",
                              resp.status_code, cid)

    # ------------------------------------------------------- Generation
    def build_params(self, model: ModelSpec | str, **params: Any) -> Dict[str, Any]:
        spec = get_model(model) if isinstance(model, str) else model
        merged = {**spec.defaults, **{k: v for k, v in params.items() if v is not None}}
        missing = [r for r in spec.required if not merged.get(r)]
        if missing:
            raise ValueError(f"{spec.key}: Pflichtfelder fehlen: {', '.join(missing)}")
        if spec.required_any and not any(merged.get(k) for k in spec.required_any):
            raise ValueError(f"{spec.key}: eines dieser Felder ist Pflicht: {', '.join(spec.required_any)}")
        if spec.duration_options and merged.get("duration") not in spec.duration_options:
            raise ValueError(f"{spec.key}: duration muss eine von {spec.duration_options} sein")
        if spec.duration_range:
            lo, hi = spec.duration_range
            if not lo <= int(merged.get("duration", lo)) <= hi:
                raise ValueError(f"{spec.key}: duration muss zwischen {lo} und {hi} s liegen")
        return merged

    def submit(self, model: ModelSpec | str, webhook_url: Optional[str] = None,
               **params: Any) -> Dict[str, Any]:
        """Job einreichen. Gibt request_id, status_url, cancel_url zurück."""
        spec = get_model(model) if isinstance(model, str) else model
        body = self.build_params(spec, **params)
        headers = {"Content-Type": "application/json",
                   "Idempotency-Key": str(uuid.uuid4())}
        query = {"hf_webhook": webhook_url} if webhook_url else None
        resp = self._request("POST", spec.path, json=body, headers=headers, params=query)
        data = self._raise_for_error(resp)
        data["estimate"] = estimate_cost(spec, body)
        return data

    def status(self, request_id: str) -> Dict[str, Any]:
        resp = self._request("GET", f"/requests/{request_id}/status")
        return self._raise_for_error(resp)

    def cancel(self, request_id: str) -> bool:
        resp = self._request("POST", f"/requests/{request_id}/cancel", retries=0)
        if resp.status_code == 202:
            return True
        if resp.status_code == 400:
            return False  # läuft schon, nicht mehr abbrechbar
        self._raise_for_error(resp)
        return False

    def wait(self, request_id: str, max_wait: float = 900.0,
             on_update=None) -> Dict[str, Any]:
        """Pollt den Status mit 2 s Start, Faktor 1,5, maximal 10 s Abstand."""
        delay, started = 2.0, time.monotonic()
        while True:
            data = self.status(request_id)
            st = str(data.get("status", "")).lower()
            if on_update:
                on_update(st, data)
            if st in TERMINAL:
                if st != "completed":
                    raise HiggsfieldError(
                        f"Job {request_id} endete mit Status '{st}': {data.get('error')}")
                return data
            if time.monotonic() - started > max_wait:
                raise HiggsfieldError(f"Job {request_id} nach {max_wait:.0f} s noch nicht fertig")
            time.sleep(delay + random.random() * 0.5)
            delay = min(delay * 1.5, 10.0)

    # ---------------------------------------------------------- Dateien
    @staticmethod
    def output_urls(result: Dict[str, Any]) -> list[str]:
        urls = []
        if result.get("video"):
            urls.append(result["video"]["url"])
        for img in result.get("images") or []:
            urls.append(img["url"])
        if result.get("audio"):
            urls.append(result["audio"]["url"])
        for a in result.get("audios") or []:
            urls.append(a["url"])
        return urls

    def download(self, result: Dict[str, Any], out_dir: str | Path = "output",
                 stem: Optional[str] = None) -> list[Path]:
        """Lädt alle Ausgaben herunter. Higgsfield hält Dateien nur mindestens 7 Tage."""
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        stem = stem or result.get("request_id", "higgsfield")
        paths = []
        for i, url in enumerate(self.output_urls(result)):
            r = requests.get(url, stream=True, timeout=self.timeout)
            r.raise_for_status()
            ext = mimetypes.guess_extension(r.headers.get("Content-Type", "").split(";")[0]) \
                or Path(url.split("?")[0]).suffix or ".bin"
            suffix = f"_{i}" if i else ""
            p = out / f"{stem}{suffix}{ext}"
            with open(p, "wb") as fh:
                for chunk in r.iter_content(1 << 16):
                    fh.write(chunk)
            paths.append(p)
        return paths

    def upload(self, file_path: str | Path, content_type: Optional[str] = None) -> str:
        """Lädt eine lokale Datei hoch und gibt die public_url für image_url & Co. zurück."""
        p = Path(file_path)
        ctype = content_type or mimetypes.guess_type(p.name)[0]
        if not ctype:
            raise ValueError(f"Content-Type für {p.name} unbekannt, bitte angeben")
        resp = self._request("POST", "/files/generate-upload-url",
                             json={"content_type": ctype},
                             headers={"Content-Type": "application/json"})
        info = self._raise_for_error(resp)
        with open(p, "rb") as fh:
            put = requests.put(info["upload_url"], data=fh,
                               headers=info.get("upload_headers", {}), timeout=300)
        put.raise_for_status()
        return info["public_url"]

    # ------------------------------------------------------- Komfort
    def generate(self, model: ModelSpec | str, out_dir: str | Path = "output",
                 on_update=None, **params: Any) -> Dict[str, Any]:
        """submit + wait + download in einem Schritt."""
        job = self.submit(model, **params)
        result = self.wait(job["request_id"], on_update=on_update)
        result["files"] = [str(p) for p in self.download(result, out_dir)]
        result["estimate"] = job["estimate"]
        return result
