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
RESOLUTION = "720p"   # 1080p kostet 2,5x (Pixel-Abrechnung), Freigabe Markentrix: 720p
SCENE = ("Helles Büro, der Sprecher steht vor einer glatten hellen Wand mit weichem "
         "Fensterlicht von der Seite, keine Bildschirme, keine Schilder")
SCRIPT = (
    "Ihre Website ist online. Anfragen bleiben aus. "
    "Sichtbarkeit allein reicht nicht. Entscheidend ist, ob daraus Anfragen entstehen. "
    "Wir bauen Websites mit einem Ziel: der Anfrage. "
    "Marken-Trix verbindet dazu Ihr Google-Profil und passende Werbung. Ein System statt Einzelmaßnahmen. "
    "Websites gibt es ab eintausendzweihundertneunzig Euro netto. "
    "Fordern Sie jetzt Ihren Website-Check an."
)
SCRIPT_TEST = "Ihre Website ist online. Anfragen bleiben aus. Marken-Trix baut daraus ein System."
SUBTITLES = [
    "Ihre Website ist online. Anfragen bleiben aus.",
    "Sichtbarkeit allein reicht nicht.",
    "Entscheidend ist,",
    "ob daraus Anfragen entstehen.",
    "Wir bauen Websites",
    "mit einem Ziel: der Anfrage.",
    "Markentrix verbindet dazu",
    "Ihr Google-Profil und passende Werbung.",
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
    res = talking_clip(c, url, SCRIPT_TEST, SCENE, duration=5, model=MODEL, resolution=RESOLUTION,
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
    res = talking_clip(c, url, SCRIPT, SCENE, duration=25, model=MODEL, resolution=RESOLUTION,
                       out_dir=OUT, name=NAME + "_master", on_update=_progress)
    (OUT / "spot-result.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    video = res["files"][0]
    print("Master:", video, post.probe(video))
    frames = post.qa_frames(video, OUT / "qa-spot", every=1)
    print("QA-Frames:", len(frames))
    segs = post.transcribe(video)
    (OUT / "transkript.json").write_text(json.dumps(segs, indent=2, ensure_ascii=False))
    print("Gehört:", " ".join(s["text"] for s in segs))


def _norm(t):
    import re
    return re.sub(r"[^a-zäöüß0-9 ]", "", t.lower().replace("ß", "ss"))


def _srt_from_transcript(duration):
    """Untertitel aus dem Skript; Zeiten aus den Transkript-Segmenten: jeder Block wird
    dem Segment zugeordnet, das die meisten seiner Wörter enthält, Segmente mit mehreren
    Blöcken werden anteilig nach Wortzahl geteilt."""
    srt = OUT / "untertitel.srt"
    tpath = OUT / "transkript.json"
    segs = json.loads(tpath.read_text()) if tpath.exists() else []
    if not segs:
        segs = [{"start": 0.0, "end": duration, "text": " ".join(SUBTITLES)}]
    assign = []
    last = 0
    for text in SUBTITLES:
        words = set(_norm(text).split())
        best, score = last, -1
        for i in range(last, len(segs)):
            sw = set(_norm(segs[i]["text"]).split())
            sc = len(words & sw) - 0.01 * (i - last)
            if sc > score:
                best, score = i, sc
        assign.append(best)
        last = best
    times = []
    for i, seg in enumerate(segs):
        idx = [k for k, a in enumerate(assign) if a == i]
        if not idx:
            continue
        total = sum(len(SUBTITLES[k].split()) for k in idx)
        t = seg["start"]
        for k in idx:
            share = (seg["end"] - seg["start"]) * len(SUBTITLES[k].split()) / total
            times.append((k, t, t + share - 0.05))
            t += share
    times.sort()

    def ts(t):
        m, s = divmod(max(t, 0), 60)
        return f"00:{int(m):02}:{int(s):02},{int((s % 1) * 1000):03}"

    lines = []
    n = 0
    hook_end = 3.0
    for k, a, b in times:
        if k == 0:
            hook_end = b + 0.05  # Block 1 trägt die Hook-Plate, kein doppelter Text
            continue
        n += 1
        lines += [str(n), f"{ts(a)} --> {ts(b)}", SUBTITLES[k], ""]
    srt.write_text("\n".join(lines), encoding="utf-8")
    srt.with_suffix(".json").write_text(json.dumps({"hook_end": round(hook_end, 2)}))
    return srt


def step_post():
    master = OUT / f"{NAME}_master.mp4"
    if not master.exists():
        sys.exit(f"Master fehlt: {master}")
    logo = _asset("markentrix-logo-light", ("svg", "png"))
    info = post.probe(master)
    srt = _srt_from_transcript(info["duration"])
    hook_png = brand.hook_plate(HOOK, OUT / "hook-plate.png", width=info["width"])
    end_png = brand.endcard(OUT / "endcard.png", logo_path=logo, cta=CTA)
    hook_end = json.loads(srt.with_suffix(".json").read_text())["hook_end"]
    v1 = post.burn_subtitles(master, srt, OUT / "_step1_subs.mp4", size=14)
    # Hook-Plate unter dem Kinn (Kopf sitzt oben im Bild), solange der Hook gesprochen wird
    v2 = post.overlay_png(v1, hook_png, OUT / "_step2_hook.mp4", start=0, end=hook_end, y="0.50*H")
    v3 = post.append_endcard(v2, end_png, OUT / "_step3_endcard.mp4", seconds=2.5)
    final = post.loudnorm(v3, OUT / f"{NAME}.mp4")
    print("Final:", final, post.probe(final))
    frames = post.qa_frames(final, OUT / "qa-final", every=2)
    print("QA-Frames final:", len(frames))


if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    {"test": step_test, "spot": step_spot, "post": step_post,
     "all": lambda: (step_test(), step_spot(), step_post())}[step]()
