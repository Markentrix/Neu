"""ElevenLabs-Voiceover für den Website-Check-Spot (eine Datei pro Szene)."""
import json, pathlib, sys, urllib.request

VOICE_ID = "ViKqgJNeCiWZlYgHiAOO"  # Markentrix Annika
OUT = pathlib.Path(__file__).resolve().parent.parent / "output" / "vo"
LINES = json.loads((pathlib.Path(__file__).parent / "skript.json").read_text())

def tts(text, path):
    body = json.dumps({
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8, "style": 0.15, "use_speaker_boost": True},
    }).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}?output_format=mp3_44100_128",
        data=body, headers={"Content-Type": "application/json", "Accept": "audio/mpeg"})
    path.write_bytes(urllib.request.urlopen(req, timeout=120).read())

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])
    for seg in LINES:
        if only and seg["id"] not in only:
            continue
        tts(seg["tts"], OUT / f"{seg['id']}.mp3")
        print("ok", seg["id"])
