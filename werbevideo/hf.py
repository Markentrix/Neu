"""Minimaler Higgsfield-REST-Client (Auth hängt der Cloud-Proxy an; lokal HF_KEY="ID:SECRET")."""
import json, os, pathlib, sys, time, uuid, urllib.request

BASE = "https://api.higgsfield.ai"

def _req(method, url, body=None, headers=None):
    h = {"Content-Type": "application/json", "User-Agent": "markentrix-video/1.0"}
    if os.environ.get("HF_KEY"):
        h["Authorization"] = f"Key {os.environ['HF_KEY']}"
    h.update(headers or {})
    data = json.dumps(body).encode() if body is not None else None
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h, method=method), timeout=120) as r:
        return json.loads(r.read() or b"{}")

def estimate(endpoint, args):
    return _req("POST", f"{BASE}/estimate/{endpoint}", args)

def submit(endpoint, args):
    return _req("POST", f"{BASE}/{endpoint}", args, {"Idempotency-Key": str(uuid.uuid4())})

def wait(status_url, timeout=1800):
    delay, t0 = 2.0, time.time()
    while True:
        r = _req("GET", status_url)
        if r["status"] in {"completed", "failed", "nsfw", "canceled"}:
            return r
        if time.time() - t0 > timeout:
            raise TimeoutError(status_url)
        time.sleep(delay)
        delay = min(delay * 1.5, 10.0)

def upload(path, content_type):
    up = _req("POST", f"{BASE}/files/generate-upload-url", {"content_type": content_type})
    req = urllib.request.Request(up["upload_url"], data=pathlib.Path(path).read_bytes(),
                                 headers=up["upload_headers"], method="PUT")
    urllib.request.urlopen(req, timeout=300).read()
    return up["public_url"]

def download(url, path):
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "markentrix-video/1.0"})
    pathlib.Path(path).write_bytes(urllib.request.urlopen(req, timeout=600).read())
