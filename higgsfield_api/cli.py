"""Kommandozeile: python -m higgsfield_api <befehl> ...

Beispiele:
  python -m higgsfield_api models
  python -m higgsfield_api estimate hailuo-t2v --duration 6
  python -m higgsfield_api video hailuo-t2v "Produkt auf Holztisch, Kamerafahrt" --duration 6
  python -m higgsfield_api video kling-std-i2v "sanfte Bewegung" --image ./foto.jpg
  python -m higgsfield_api image soul "Portrait, weiches Tageslicht" --aspect 9:16
  python -m higgsfield_api host                       # Host-Bild für UGC-Serie
  python -m higgsfield_api clip output/host/<id>.png "Anfragen kommen. Und gehen wieder unter. ..." --duration 15
  python -m higgsfield_api frames output/clip.mp4     # QA-Standbilder
  python -m higgsfield_api transcribe output/clip.mp4 --script "..."   # Aussprache prüfen
  python -m higgsfield_api status <request_id>
  python -m higgsfield_api check
"""

import argparse
import json
import sys

from .client import HiggsfieldClient, HiggsfieldError
from .models import MODELS, get_model
from .pricing import estimate_cost, format_estimate
from . import ugc, post


def _progress(st, _data):
    print(f"  status: {st}", file=sys.stderr)


def cmd_models(_args):
    for spec in MODELS.values():
        print(f"{spec.key:14} {spec.kind:5} {spec.list_price_usd:.4f} USD/{spec.unit:6} {spec.description}")


def cmd_estimate(args):
    params = _params(args)
    print(format_estimate(estimate_cost(args.model, params)))


def cmd_check(_args):
    """Kostenloser Verbindungstest: 404 bedeutet, der Schlüssel wird akzeptiert."""
    c = HiggsfieldClient()
    try:
        c.status("00000000-0000-0000-0000-000000000000")
    except HiggsfieldError as e:
        if e.status_code == 404:
            print("OK: API erreichbar, Zugangsdaten akzeptiert.")
            return
        print(f"FEHLER: {e}")
        sys.exit(1)
    print("Unerwartet: Status einer erfundenen ID gefunden.")


def _params(args):
    p = {}
    for name in ("duration", "aspect", "resolution", "num_images", "cfg_scale", "negative_prompt"):
        v = getattr(args, name, None)
        if v is not None:
            p["aspect_ratio" if name == "aspect" else name] = v
    return p


def _run_generation(args, kind):
    spec = get_model(args.model)
    if spec.kind != kind:
        sys.exit(f"{args.model} ist ein {spec.kind}-Modell, kein {kind}-Modell")
    c = HiggsfieldClient()
    params = _params(args)
    params["prompt"] = args.prompt
    if getattr(args, "image", None):
        if args.image.startswith("http"):
            params["image_url"] = args.image
        else:
            print("Lade Bild hoch ...", file=sys.stderr)
            params["image_url"] = c.upload(args.image)
    body = c.build_params(spec, **params)
    est = estimate_cost(spec, body)
    print("Schätzung:", format_estimate(est), file=sys.stderr)
    if args.dry_run:
        print(json.dumps({"path": spec.path, "body": body, "estimate": est}, indent=2, ensure_ascii=False))
        return
    job = c.submit(spec, **body)
    print(f"Request-ID: {job['request_id']}", file=sys.stderr)
    result = c.wait(job["request_id"], on_update=_progress)
    files = c.download(result, args.out, stem=args.name)
    print(json.dumps({"request_id": job["request_id"], "files": [str(f) for f in files],
                      "urls": c.output_urls(result), "estimate": est}, indent=2, ensure_ascii=False))


def cmd_host(args):
    c = HiggsfieldClient()
    if args.dry_run:
        body = c.build_params("soul2", prompt=args.look or ugc.HOST_LOOK, batch_size=args.batch)
        print(json.dumps({"body": body, "estimate": estimate_cost("soul2", body)}, indent=2, ensure_ascii=False))
        return
    meta = ugc.create_host(c, out_dir=args.out, look=args.look or ugc.HOST_LOOK,
                           seed=args.seed, batch_size=args.batch)
    print(json.dumps(meta, indent=2, ensure_ascii=False))


def cmd_clip(args):
    c = HiggsfieldClient()
    host = args.host
    if not host.startswith("http"):
        print("Lade Host-Bild hoch ...", file=sys.stderr)
        host = c.upload(host)
    audio = args.audio
    if audio and not audio.startswith("http"):
        print("Lade Tonspur hoch ...", file=sys.stderr)
        audio = c.upload(audio)
    res = ugc.talking_clip(c, host, args.script, args.scene, duration=args.duration,
                           model=args.model, audio_url=audio, out_dir=args.out,
                           name=args.name, dry_run=args.dry_run, on_update=_progress)
    print(json.dumps(res, indent=2, ensure_ascii=False))


def cmd_frames(args):
    frames = post.qa_frames(args.video, args.out, every=args.every)
    print(json.dumps({"probe": post.probe(args.video), "frames": [str(f) for f in frames]}, indent=2))


def cmd_transcribe(args):
    segs = post.transcribe(args.video, language=args.language)
    for s in segs:
        print(f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}")
    if args.script:
        print("\nSkript:   ", " ".join(args.script.split()))
        print("Gehört:   ", " ".join(s["text"] for s in segs))


def cmd_status(args):
    c = HiggsfieldClient()
    data = c.status(args.request_id)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    if args.download and str(data.get("status", "")).lower() == "completed":
        for p in c.download(data, args.out):
            print("gespeichert:", p)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="higgsfield_api", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("models", help="bekannte Modelle und Listenpreise").set_defaults(fn=cmd_models)
    sub.add_parser("check", help="kostenloser Verbindungstest").set_defaults(fn=cmd_check)

    def gen_args(p):
        p.add_argument("model")
        p.add_argument("prompt")
        p.add_argument("--duration", type=int)
        p.add_argument("--aspect", help="z.B. 9:16")
        p.add_argument("--resolution", help="2K oder 4K (nur Bild)")
        p.add_argument("--num-images", dest="num_images", type=int)
        p.add_argument("--cfg-scale", dest="cfg_scale", type=float)
        p.add_argument("--negative-prompt", dest="negative_prompt")
        p.add_argument("--out", default="output")
        p.add_argument("--name", help="Dateiname ohne Endung")
        p.add_argument("--dry-run", action="store_true", help="nur Schätzung und Request anzeigen")

    pe = sub.add_parser("estimate", help="Kosten schätzen, ohne etwas zu senden")
    pe.add_argument("model"); pe.add_argument("--duration", type=int); pe.add_argument("--num-images", dest="num_images", type=int)
    pe.set_defaults(fn=cmd_estimate)

    pv = sub.add_parser("video", help="Video erzeugen"); gen_args(pv)
    pv.add_argument("--image", help="Startbild: lokale Datei oder URL")
    pv.set_defaults(fn=lambda a: _run_generation(a, "video"))

    pi = sub.add_parser("image", help="Bild erzeugen"); gen_args(pi)
    pi.set_defaults(fn=lambda a: _run_generation(a, "image"))

    ph = sub.add_parser("host", help="Host-Bild (SOUL V2, 9:16) erzeugen")
    ph.add_argument("--look", help="eigener Look-Prompt, sonst Markentrix-Standard")
    ph.add_argument("--seed", type=int); ph.add_argument("--batch", type=int, default=1, choices=[1, 4])
    ph.add_argument("--out", default="output/host"); ph.add_argument("--dry-run", action="store_true")
    ph.set_defaults(fn=cmd_host)

    pc = sub.add_parser("clip", help="Sprecher-Clip mit deutschem Text rendern")
    pc.add_argument("host", help="Host-Bild: lokale Datei oder URL")
    pc.add_argument("script", help="gesprochener Text, wörtlich")
    pc.add_argument("--scene", default="Helles Büro mit Fensterlicht, ruhiger Hintergrund")
    pc.add_argument("--duration", type=int, default=15)
    pc.add_argument("--model", default="seedance2-ref", help="seedance2-ref, seedance25-ref, kling3-std-i2v, kling3-pro-i2v")
    pc.add_argument("--audio", help="eigene Tonspur (wav/mp4) als Datei oder URL, nur Seedance")
    pc.add_argument("--out", default="output"); pc.add_argument("--name"); pc.add_argument("--dry-run", action="store_true")
    pc.set_defaults(fn=cmd_clip)

    pf = sub.add_parser("frames", help="QA-Standbilder aus einem Video ziehen")
    pf.add_argument("video"); pf.add_argument("--out", default="output/qa"); pf.add_argument("--every", type=float, default=1.0)
    pf.set_defaults(fn=cmd_frames)

    pt = sub.add_parser("transcribe", help="Tonspur transkribieren (Aussprache-Gate)")
    pt.add_argument("video"); pt.add_argument("--language", default="de"); pt.add_argument("--script", help="Soll-Text zum Vergleich")
    pt.set_defaults(fn=cmd_transcribe)

    ps = sub.add_parser("status", help="Status abfragen, optional herunterladen")
    ps.add_argument("request_id"); ps.add_argument("--download", action="store_true"); ps.add_argument("--out", default="output")
    ps.set_defaults(fn=cmd_status)

    args = ap.parse_args(argv)
    try:
        args.fn(args)
    except HiggsfieldError as e:
        extra = f" (Correlation-ID {e.correlation_id})" if e.correlation_id else ""
        sys.exit(f"Higgsfield-Fehler: {e}{extra}")
    except (ValueError, KeyError) as e:
        sys.exit(f"Fehler: {e}")


if __name__ == "__main__":
    main()
