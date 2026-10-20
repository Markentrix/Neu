"""Host-Hook (5 s): Seedance 2.0 reference-to-video, lippensynchron zur ElevenLabs-Spur."""
import json, pathlib, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import hf

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "output"
ENDPOINT = "bytedance/seedance-2.0/reference-to-video"
TEXT = json.loads((ROOT / "werbevideo" / "skript.json").read_text())[0]["text"]

def build_audio():
    # 0,3 s Vorlauf, leicht gestrafft (1,05), auf exakt 5,0 s aufgefüllt
    wav = OUT / "vo" / "s0_hook_5s.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / "vo" / "s0_hook.trim.wav"),
                    "-af", "atempo=1.05,adelay=300:all=1,apad", "-t", "5.0", "-ar", "44100", "-ac", "1", str(wav)], check=True)
    return wav

if __name__ == "__main__":
    wav = build_audio()
    args = {
        "prompt": (
            "Die Frau aus dem Referenzbild spricht ruhig, freundlich und direkt in die Kamera, exakt lippensynchron zur "
            f"Referenz-Tonspur. Sie sagt wörtlich auf Deutsch: „{TEXT}“ Natürliche, leichte Kopfbewegungen, kurzes "
            "Lächeln am Ende, Hände außerhalb des Bildes. Statische Smartphone-Kamera, helles Büro mit Tageslicht, "
            "gleiche Person, gleiche Kleidung, kein Text, keine Logos, keine Untertitel."
        ),
        "image_urls": [hf.upload(OUT / "host" / "host_markentrix.png", "image/png")],
        "audio_urls": [hf.upload(wav, "audio/wav")],
        "duration": 5, "resolution": "1080p", "aspect_ratio": "9:16", "generate_audio": True,
    }
    sub = hf.submit(ENDPOINT, args)
    print("submitted", sub["request_id"], flush=True)
    r = hf.wait(sub["status_url"])
    print(r["status"], r["request_id"])
    (OUT / "clips").mkdir(exist_ok=True)
    (OUT / "clips" / "hook-meta.json").write_text(json.dumps({"request": r, "args": args}, indent=2, ensure_ascii=False))
    if r["status"] == "completed":
        hf.download(r["video"]["url"], OUT / "clips" / "MKT_VIDEO_A_WebsiteCheck_H1_hook_5s_v1.mp4")
