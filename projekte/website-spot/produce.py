"""Produktion des Website-Spots (Typ A, Gründer-Format, 25 s, Seedance 2.5).

Ablauf (jeder Schritt einzeln aufrufbar):
  python projekte/website-spot/produce.py test      # 5-s-Testclip, Aussprache + Lippen prüfen
  python projekte/website-spot/produce.py spot      # 25-s-Spot rendern, QA-Frames, Transkript
  python projekte/website-spot/produce.py post      # Untertitel, Hook-Plate, Endcard, Master + Final
  python projekte/website-spot/produce.py all

Voraussetzungen: assets/host/kitz.(jpg|png), assets/markentrix-logo-light.(svg|png)
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from higgsfield_api import HiggsfieldClient, brand, post  # noqa: E402
from higgsfield_api.ugc import talking_clip  # noqa: E402

OUT = ROOT / "output" / "website-spot"
NAME = "MKT_VIDEO_A_Lokal_H1_25s_v1_2026-10-08"
MODEL = "seedance25-ref"
SCENE = ("Helles Büro, der Sprecher steht vor einer glatten hellen Wand mit weichem "
         "Fensterlicht von der Seite, keine Bildschirme, keine Schilder")
SCRIPT = (
    "Ihre Website ist online. Anfragen bleiben aus. "
    "Sichtbarkeit allein reicht nicht. Entscheidend ist, ob daraus Anfragen entstehen. "
    "Wir bauen Websites mit einem Ziel: der Anfrage. "
    "Mar-ken-triks verbindet dazu Ihr Google-Profil und passende Werbung. Ein System statt Einzelmaßnahmen. "
    "Websites gibt es ab eintausendzweihundertneunzig Euro netto. "
    "Fordern Sie jetzt Ihren Website-Check an."
)
SCRIPT_TEST = "Ihre Website ist online. Anfragen bleiben aus. Mar-ken-triks baut daraus ein System."
SUBTITLES = [
    "Ihre Website ist online. Anfragen bleiben aus.",
    "Sichtbarkeit allein reicht nicht.",
    "Entscheidend ist, ob daraus Anfragen entstehen.",
    "Wir bauen Websites mit einem Ziel: der Anfrage.",
    "Markentrix verbindet dazu Ihr Google-Profil und passende Werbung.",
    "Ein System statt Einzelmaßnahmen.",
    "Websites ab 1.290 € netto.",
    "Fordern Sie jetzt Ihren Website-Check an.",
]
HOOK = "Ihre Website ist online. Anfragen bleiben aus."
CTA = "Website-Check anfragen →"


def _asset(stem, exts):
    for e in exts:
        p = ROOT / "assets" / f"{stem}.{e}"
        if p.exists():
            return p
    sys.exit(f"Fehlt: assets/{stem}.{'|'.join(exts)}")


def _host_url(c):
    cache = OUT / "host-url.json"
    if cache.exists():
        return json.loads(cache.read_text())["url"]
    photo = _asset("host/kitz", ("jpg", "jpeg", "png"))
    url = c.upload(photo)
    OUT.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"url": url, "file": str(photo)}))
    return url


def _progress(st, _d):
    print(f"  status: {st}", file=sys.stderr)


def step_test():
    c = HiggsfieldClient()
    url = _host_url(c)
    res = talking_clip(c, url, SCRIPT_TEST, SCENE, duration=5, model=MODEL,
                       out_dir=OUT, name="test-aussprache", on_update=_progress)
    print(json.dumps(res["estimate"], indent=1))
    video = res["files"][0]
    frames = post.qa_frames(video, OUT / "qa-test", every=1)
    print("QA-Frames:", len(frames))
    segs = post.transcribe(video)
    print("Gehört:", " ".join(s["text"] for s in segs))
    print("Soll:  ", SCRIPT_TEST)


def step_spot():
    c = HiggsfieldClient()
    url = _host_url(c)
    res = talking_clip(c, url, SCRIPT, SCENE, duration=25, model=MODEL,
                       out_dir=OUT, name=NAME + "_master", on_update=_progress)
    (OUT / "spot-result.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    video = res["files"][0]
    print("Master:", video, post.probe(video))
    frames = post.qa_frames(video, OUT / "qa-spot", every=1)
    print("QA-Frames:", len(frames))
    segs = post.transcribe(video)
    (OUT / "transkript.json").write_text(json.dumps(segs, indent=2, ensure_ascii=False))
    print("Gehört:", " ".join(s["text"] for s in segs))


def _srt_from_transcript(duration):
    """Untertitel aus dem Skript, Zeiten aus der Transkription (gleichmäßig je Block)."""
    srt = OUT / "untertitel.srt"
    tpath = OUT / "transkript.json"
    segs = json.loads(tpath.read_text()) if tpath.exists() else []
    speech_start = segs[0]["start"] if segs else 0.0
    speech_end = segs[-1]["end"] if segs else duration
    per = (speech_end - speech_start) / len(SUBTITLES)

    def ts(t):
        m, s = divmod(max(t, 0), 60)
        return f"00:{int(m):02}:{int(s):02},{int((s % 1) * 1000):03}"

    lines = []
    for i, text in enumerate(SUBTITLES, 1):
        a, b = speech_start + (i - 1) * per, speech_start + i * per - 0.05
        lines += [str(i), f"{ts(a)} --> {ts(b)}", text, ""]
    srt.write_text("\n".join(lines), encoding="utf-8")
    return srt


def step_post():
    master = OUT / f"{NAME}_master.mp4"
    if not master.exists():
        sys.exit(f"Master fehlt: {master}")
    logo = _asset("markentrix-logo-light", ("svg", "png"))
    info = post.probe(master)
    srt = _srt_from_transcript(info["duration"])
    hook_png = brand.hook_plate(HOOK, OUT / "hook-plate.png")
    end_png = brand.endcard(OUT / "endcard.png", logo_path=logo, cta=CTA)
    v1 = post.burn_subtitles(master, srt, OUT / "_step1_subs.mp4")
    v2 = post.overlay_png(v1, hook_png, OUT / "_step2_hook.mp4", start=0, end=3, y="260")
    final = post.append_endcard(v2, end_png, OUT / f"{NAME}.mp4", seconds=2.5)
    print("Final:", final, post.probe(final))
    frames = post.qa_frames(final, OUT / "qa-final", every=2)
    print("QA-Frames final:", len(frames))


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    {"test": step_test, "spot": step_spot, "post": step_post,
     "all": lambda: (step_test(), step_spot(), step_post())}[step]()
