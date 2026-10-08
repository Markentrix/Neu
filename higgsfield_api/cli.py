"""Kommandozeile: python -m higgsfield_api <befehl> ...

Beispiele:
  python -m higgsfield_api models
  python -m higgsfield_api estimate hailuo-t2v --duration 6
  python -m higgsfield_api video hailuo-t2v "Produkt auf Holztisch, Kamerafahrt" --duration 6
  python -m higgsfield_api video kling-std-i2v "sanfte Bewegung" --image ./foto.jpg
  python -m higgsfield_api image soul "Portrait, weiches Tageslicht" --aspect 9:16
  python -m higgsfield_api status <request_id>
  python -m higgsfield_api check
"""

import argparse
import json
import sys

from .client import HiggsfieldClient, HiggsfieldError
from .models import MODELS, get_model
from .pricing import estimate_cost, format_estimate


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
