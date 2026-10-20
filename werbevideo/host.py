"""Host-Bild (SOUL V2, 9:16) für den Website-Check-Spot."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import hf

OUT = pathlib.Path(__file__).resolve().parent.parent / "output" / "host"
PROMPT = (
    "Vertical smartphone photo, natural daylight UGC style. A friendly, professional German woman, about 35 years old, "
    "shoulder-length dark blonde hair, natural light makeup, wearing a plain navy blazer over a plain white t-shirt, "
    "no jewelry logos, no lanyard, no badge. She sits at a clean bright desk in a modern minimal office with large windows, "
    "soft white walls, a small green plant, blurred calm background, no screens, no signs, no text, no logos. "
    "She looks directly into the camera with a calm, slight confident smile, mouth closed, chest-up framing, centered, "
    "head in the upper third of the frame. Realistic skin texture, correct anatomy, editorial yet authentic."
)
ARGS = {"prompt": PROMPT, "aspect_ratio": "9:16", "resolution": "1080p", "batch_size": 4}

if __name__ == "__main__":
    print("Kosten:", hf.estimate("higgsfield-ai/soul/v2/standard", ARGS))
    if "--dry-run" in sys.argv:
        sys.exit()
    r = hf.wait(hf.submit("higgsfield-ai/soul/v2/standard", ARGS)["status_url"])
    print(r["status"], r["request_id"])
    meta = []
    for i, img in enumerate(r.get("images", [])):
        p = OUT / f"host_kandidat_{i+1}.png"
        hf.download(img["url"], p)
        meta.append({"file": p.name, "url": img["url"]})
    (OUT / "host-meta.json").write_text(json.dumps({"request_id": r["request_id"], "args": ARGS, "images": meta}, indent=2, ensure_ascii=False))
