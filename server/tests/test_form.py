#!/usr/bin/env python3
"""Prüft den Anfrage-Endpunkt gegen einen echten PHP-Server und einen Test-Mailserver.

Aufruf (aus dem Projektordner):  python3 server/tests/test_form.py
Voraussetzung: php (mit gd), openssl und Pillow (pip install pillow).
"""
import email
import email.policy
import http.client
import io
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

sys.path.insert(0, os.path.dirname(__file__))
from smtp_sink import Sink  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PUBLIC = os.path.join(ROOT, "public")
results = []


def check(name, cond, detail=""):
    results.append((name, bool(cond)))
    print(("  ok     " if cond else "  FEHLER ") + name + (f"   [{detail}]" if detail and not cond else ""))


# ------------------------------------------------------------------ Hilfen

def write_config(priv, sink_port, **over):
    cfg = {
        "secret": "t" * 40, "mail_to": "info@psschneider.de", "mail_from": "anfragen@psschneider.de",
        "smtp": {"host": "127.0.0.1", "port": sink_port, "secure": "starttls", "user": "anfragen@psschneider.de",
                 "pass": "geheim", "verify_peer": False, "timeout": 5},
        "allowed_origins": [], "min_seconds": 1, "rate_per_hour": 1000, "rate_per_day": 1000,
        "max_photo_mb": 3, "keep_failed_days": 0,
    }
    cfg.update(over)
    os.makedirs(priv, exist_ok=True)
    with open(os.path.join(priv, "config.php"), "w") as f:
        f.write("<?php return json_decode(" + "'" + json.dumps(cfg).replace("\\", "\\\\").replace("'", "\\'") + "'" + ", true);\n")


class Server:
    def __init__(self, port, sink_port, post_max="60M", **over):
        self.port, self.priv = port, tempfile.mkdtemp(prefix="priv-")
        self.origin = f"http://127.0.0.1:{port}"
        write_config(self.priv, sink_port, allowed_origins=[self.origin], **over)
        env = dict(os.environ, PSS_PRIVATE_DIR=self.priv)
        self.proc = subprocess.Popen(
            ["php", "-d", "upload_max_filesize=20M", "-d", f"post_max_size={post_max}", "-d", "max_file_uploads=20",
             "-S", f"127.0.0.1:{port}", "-t", PUBLIC], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(50):
            try:
                http.client.HTTPConnection("127.0.0.1", port, timeout=1).request("GET", "/")
                break
            except OSError:
                time.sleep(0.1)

    def stop(self):
        self.proc.terminate()
        self.proc.wait()

    def request(self, method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=30)
        c.request(method, path, body=body, headers=headers or {})
        r = c.getresponse()
        raw = r.read()
        try:
            return r.status, json.loads(raw)
        except ValueError:
            return r.status, raw

    def token(self):
        return self.request("GET", "/api/anfrage.php?aktion=token")[1]["token"]

    def post(self, fields, files=(), origin="auto", extra=None):
        body, ctype = multipart(fields, files)
        h = {"Content-Type": ctype}
        if origin == "auto":
            h["Origin"] = self.origin
        elif origin:
            h["Origin"] = origin
        h.update(extra or {})
        return self.request("POST", "/api/anfrage.php", body, h)

    def inbox(self):
        d = os.path.join(self.priv, "inbox")
        return sorted(os.listdir(d)) if os.path.isdir(d) else []

    def log(self):
        p = os.path.join(self.priv, "logs", "anfragen.log")
        return open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def multipart(fields, files):
    b = uuid.uuid4().hex
    out = bytearray()
    for k, v in fields.items():
        out += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n'.encode() + v.encode() + b"\r\n"
    for name, content, ctype in files:
        out += (f'--{b}\r\nContent-Disposition: form-data; name="photos[]"; filename="{name}"\r\n'
                f"Content-Type: {ctype}\r\n\r\n").encode() + content + b"\r\n"
    out += f"--{b}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={b}"


def jpeg(w, h, exif=None, noise=False, quality=90):
    im = Image.new("RGB", (w, h), (200, 60, 40))
    if noise:
        rnd = random.Random(1)
        im.putdata([(rnd.randrange(256), rnd.randrange(256), rnd.randrange(256)) for _ in range(w * h)])
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, **({"exif": exif} if exif else {}))
    return buf.getvalue()


def gps_exif(orientation=1):
    ex = Image.Exif()
    ex[0x0112] = orientation
    ex[0x8825] = {1: "N", 2: (52.0, 37.0, 21.0), 3: "E", 4: (10.0, 4.0, 50.0)}
    return ex.tobytes()


def fields(token, **over):
    f = {"name": "Max Müller", "email": "max@example.de", "phone": "0511 123456", "subject": "Haftpflichtschaden-Gutachten",
         "message": "Auffahrunfall am Montag, Heck beschädigt.\nBitte um Termin.", "consent": "1", "token": token, "website": ""}
    f.update(over)
    return f


def parse(sink, n=-1):
    return email.message_from_bytes(sink.messages[n]["raw"], policy=email.policy.default)


# ------------------------------------------------------------------ Tests

def main():
    sink = Sink()
    srv = Server(8101, sink.port)
    try:
        print("Token und Grundfälle")
        st, j = srv.request("GET", "/api/anfrage.php")
        check("GET ohne Aktion wird abgelehnt (405)", st == 405)
        tok = srv.token()
        check("Token wird ausgegeben", "." in tok)
        time.sleep(1.3)

        print("\nNormale Anfrage ohne Fotos")
        st, j = srv.post(fields(tok))
        check("Antwort 200 mit Referenz", st == 200 and j.get("ok") and len(j.get("ref", "")) == 8, str(j))
        check("genau eine Mail kam an", len(sink.messages) == 1)
        m = parse(sink)
        body = m.get_body(preferencelist=("plain",)).get_content()
        check("Absender, Empfänger und Antwortadresse stimmen",
              sink.messages[0]["from_"] == "anfragen@psschneider.de" and sink.messages[0]["to"] == ["info@psschneider.de"]
              and m["Reply-To"] == "max@example.de", f"{sink.messages[0]['from_']} {m['Reply-To']}")
        check("Betreff enthält Anliegen und Name mit Umlauten", "Haftpflichtschaden-Gutachten" in m["Subject"] and "Max Müller" in m["Subject"], m["Subject"])
        check("Text enthält Name, Telefon, Nachricht und Referenz", all(x in body for x in ("Max Müller", "0511 123456", "Auffahrunfall am Montag", j["ref"])), body)
        check("Kein Zwischenspeicher bleibt zurück", srv.inbox() == [])
        check("Keine IP-Adresse und kein Name im Log", "127.0.0.1" not in srv.log() and "Müller" not in srv.log() and "ok ref=" in srv.log(), srv.log())

        print("\nFotos")
        big = jpeg(4000, 3000, exif=gps_exif(6))
        check("Testfoto enthält Standortdaten", Image.open(io.BytesIO(big)).getexif().get_ifd(0x8825) != {})
        png = io.BytesIO()
        Image.new("RGBA", (300, 200), (10, 120, 240, 90)).save(png, "PNG")
        st, j = srv.post(fields(tok), [("schaden1.jpg", big, "image/jpeg"), ("schaden2.png", png.getvalue(), "image/png")])
        check("Zwei Fotos werden angenommen", st == 200 and j.get("ok"), str(j))
        m = parse(sink)
        atts = list(m.iter_attachments())
        check("Zwei Anhänge foto-1.jpg und foto-2.jpg", [a.get_filename() for a in atts] == ["foto-1.jpg", "foto-2.jpg"], str([a.get_filename() for a in atts]))
        a1 = Image.open(io.BytesIO(atts[0].get_content()))
        check("Anhang 1 ist JPEG, auf 2400 Pixel verkleinert und gedreht (Hochformat)", a1.format == "JPEG" and max(a1.size) == 2400 and a1.size[1] > a1.size[0], str(a1.size))
        check("Standortdaten sind entfernt", a1.getexif().get_ifd(0x8825) == {} and 0x0112 not in a1.getexif(), str(dict(a1.getexif())))
        a2 = Image.open(io.BytesIO(atts[1].get_content()))
        check("PNG wurde zu JPEG ohne Transparenz", a2.format == "JPEG" and a2.mode == "RGB")
        check("Mail mit Fotos nennt Anzahl im Text", "2 Anhang" in m.get_body(preferencelist=("plain",)).get_content())

        print("\nUnzulässige Dateien")
        for label, name, content, ctype in [
            ("Textdatei als .jpg getarnt", "a.jpg", b"das ist kein Bild", "image/jpeg"),
            ("PHP-Code als .jpg getarnt", "a.jpg", b"<?php system($_GET['c']); ?>", "image/jpeg"),
            ("GIF", "a.gif", b"GIF89a" + b"\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;", "image/gif"),
            ("SVG mit Skript", "a.svg", b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>", "image/svg+xml"),
            ("JPEG mit angehängtem PHP wird nur als Bild neu gespeichert", None, None, None),
        ]:
            if name is None:
                poly = jpeg(200, 100) + b"<?php echo 'x'; ?>"
                n_before = len(sink.messages)
                st, j = srv.post(fields(tok), [("p.jpg", poly, "image/jpeg")])
                if st == 200:
                    att = list(parse(sink).iter_attachments())[0].get_content()
                    check(label, b"<?php" not in att and Image.open(io.BytesIO(att)).format == "JPEG")
                else:
                    check(label, True)
                continue
            st, j = srv.post(fields(tok), [(name, content, ctype)])
            check(f"{label} wird abgelehnt (400)", st == 400 and "photos" in j.get("errors", {}), f"{st} {j}")
        st, j = srv.post(fields(tok), [(f"f{i}.jpg", jpeg(50, 50), "image/jpeg") for i in range(6)])
        check("Sechs Fotos werden abgelehnt", st == 400 and "photos" in j.get("errors", {}), f"{st} {j}")
        st, j = srv.post(fields(tok), [("riesig.jpg", jpeg(1800, 1800, noise=True, quality=100), "image/jpeg")])
        check("Foto über dem Größenlimit wird abgelehnt", st == 400 and "zu groß" in j.get("error", ""), f"{st} {j.get('error')}")
        check("Nach Fehlern bleibt nichts zwischengespeichert", srv.inbox() == [])

        print("\nEingaben")
        n = len(sink.messages)
        for label, over, field in [
            ("Name fehlt", {"name": ""}, "name"), ("E-Mail ungültig", {"email": "kaputt"}, "email"),
            ("Anliegen fehlt", {"subject": ""}, "subject"), ("Nachricht zu kurz", {"message": "hi"}, "message"),
            ("Zustimmung fehlt", {"consent": ""}, "consent"),
        ]:
            st, j = srv.post(fields(tok, **over))
            check(f"{label}: 400 mit Feldfehler", st == 400 and field in j.get("errors", {}), f"{st} {j}")
        check("Bei Fehlern wird keine Mail verschickt", len(sink.messages) == n)
        st, j = srv.post(fields(tok, name="Max\r\nBcc: boese@example.com", subject="Test\r\nBcc: x@y.de"))
        m = parse(sink)
        check("Kopfzeilen-Einschleusung: Anfrage geht durch, aber ohne Bcc-Zeile", st == 200 and m["Bcc"] is None, f"{st} {list(m.keys())}")
        check("Zeilenumbrüche im Betreff sind entfernt", "\n" not in str(m["Subject"]) and "\r" not in str(m["Subject"]))
        st, j = srv.post(fields(tok, message="Zeile1\n.\nZeile3\r\n.\r\nEnde"))
        check("Zeile mit einzelnem Punkt kommt unversehrt an", st == 200 and "Zeile3" in parse(sink).get_body(preferencelist=("plain",)).get_content())
        st, j = srv.post(fields(tok, message="ü" * 6000))
        check("Sehr lange Nachricht wird gekürzt statt abgelehnt", st == 200 and len(parse(sink).get_body(preferencelist=("plain",)).get_content()) < 6000)

        print("\nSpam- und Missbrauchsschutz")
        n = len(sink.messages)
        st, j = srv.post(fields(tok, website="http://spam.example"))
        check("Köderfeld: scheinbar Erfolg, aber keine Mail", st == 200 and j.get("ok") and len(sink.messages) == n)
        st, j = srv.post(fields(""))
        check("Ohne Token wird abgelehnt", st == 400, f"{st} {j}")
        st, j = srv.post(fields("123.abc"))
        check("Gefälschtes Token wird abgelehnt", st == 400)
        st, j = srv.post(fields(tok.split(".")[0] + ".0" * 1))
        check("Token mit falscher Signatur wird abgelehnt", st == 400)
        fresh = srv.token()
        st, j = srv.post(fields(fresh))
        check("Sofort abgeschicktes Formular ist zu schnell (400)", st == 400 and "schnell" in j.get("error", ""), f"{st} {j}")
        st, j = srv.post(fields(tok), origin="https://boese.example")
        check("Fremde Herkunft wird abgelehnt (403)", st == 403)
        st, j = srv.post(fields(tok), origin=None)
        check("Ohne Herkunftsangabe wird abgelehnt (403)", st == 403)
        st, j = srv.post(fields(tok), origin=None, extra={"Referer": srv.origin + "/kontakt/"})
        check("Mit passendem Referer ohne Origin wird angenommen", st == 200, f"{st} {j}")
        st, j = srv.request("PUT", "/api/anfrage.php", b"x", {"Origin": srv.origin})
        check("PUT wird abgelehnt (405)", st == 405)
        n = len(sink.messages)
        st, j = srv.request("GET", "/../private/config.php")
        check("Konfiguration ist nicht per Web erreichbar", b"secret" not in (j if isinstance(j, bytes) else json.dumps(j).encode()))

        print("\nVersandfehler")
        sink.fail_data = True
        st, j = srv.post(fields(tok))
        check("Mailserver lehnt ab: 502 mit Referenz", st == 502 and j.get("ref"), f"{st} {j}")
        check("Anfrage bleibt zur Wiederherstellung gespeichert", len(srv.inbox()) == 1 and os.path.exists(os.path.join(srv.priv, "inbox", srv.inbox()[0], "anfrage.json")))
        check("Fehler steht im Log ohne Passwort", "mail_fehler" in srv.log() and "geheim" not in srv.log(), srv.log())
        sink.fail_data = False
        r = subprocess.run(["php", os.path.join(PUBLIC, "api", "anfrage.php"), "purge"], env=dict(os.environ, PSS_PRIVATE_DIR=srv.priv), capture_output=True, text=True)
        check("purge löscht den alten Zwischenspeicher (keep_failed_days=0)", srv.inbox() == [] and '"inbox":1' in r.stdout, r.stdout + r.stderr)
        sink.user = "anders@example.com"
        st, j = srv.post(fields(tok))
        check("Falsches SMTP-Passwort: 502 und Passwort nicht im Log", st == 502 and "geheim" not in srv.log() and sink.auth_failures >= 1, f"{st} {j}")
        sink.user = "anfragen@psschneider.de"
        srv.stop()
        srv = Server(8105, 1)  # Mailserver nicht erreichbar
        tok2 = srv.token()
        time.sleep(1.3)
        st, j = srv.post(fields(tok2))
        check("Mailserver nicht erreichbar: 502 und Anfrage bleibt gespeichert", st == 502 and len(srv.inbox()) == 1, f"{st} {j}")
        srv.stop()

        print("\nSelbsttest und Mengenbegrenzung")
        srv = Server(8102, sink.port)
        ini = ["-d", "upload_max_filesize=20M", "-d", "post_max_size=60M", "-d", "max_file_uploads=20"]
        r = subprocess.run(["php", *ini, os.path.join(PUBLIC, "api", "anfrage.php"), "selftest"],
                           env=dict(os.environ, PSS_PRIVATE_DIR=srv.priv), capture_output=True, text=True)
        check("selftest meldet alles bereit", r.returncode == 0 and "Alles bereit" in r.stdout, r.stdout[-400:])
        r = subprocess.run(["php", os.path.join(PUBLIC, "api", "anfrage.php"), "selftest"],
                           env=dict(os.environ, PSS_PRIVATE_DIR=srv.priv), capture_output=True, text=True)
        check("selftest meldet zu kleine Upload-Grenzen als Fehler", r.returncode == 1 and "upload_max_filesize" in r.stdout and "FEHLER" in r.stdout)
        r = subprocess.run(["php", *ini, os.path.join(PUBLIC, "api", "anfrage.php"), "selftest"],
                           env=dict(os.environ, PSS_PRIVATE_DIR="/nicht/vorhanden"), capture_output=True, text=True)
        check("selftest meldet fehlende Konfiguration als Fehler", r.returncode == 1 and "Konfiguration" in r.stdout)
        srv.stop()
        srv = Server(8103, sink.port, rate_per_hour=3)
        tok = srv.token()
        time.sleep(1.3)
        codes = [srv.post(fields(tok))[0] for _ in range(5)]
        check("Nach drei Anfragen pro Stunde kommt 429", codes == [200, 200, 200, 429, 429], str(codes))
        rl = os.path.join(srv.priv, "ratelimit")
        check("Mengenzähler enthält keine Klartext-IP", all("127.0.0.1" not in f and "127.0.0.1" not in open(os.path.join(rl, f)).read() for f in os.listdir(rl)))
        srv.stop()

        print("\nSehr große Anfrage")
        srv = Server(8104, sink.port, post_max="1M")
        tok = srv.token()
        time.sleep(1.3)
        st, j = srv.post(fields(tok), [("a.jpg", jpeg(1500, 1500, noise=True, quality=95), "image/jpeg")])
        check("Über post_max_size: 413 mit verständlicher Meldung", st == 413 and "zu groß" in j.get("error", ""), f"{st} {j}")
        srv.stop()
    finally:
        try:
            srv.stop()
        except Exception:
            pass
        sink.close()

    bad = [n for n, ok in results if not ok]
    print(f"\n{len(results) - len(bad)} von {len(results)} Prüfungen bestanden.")
    if bad:
        print("Fehlgeschlagen:", *bad, sep="\n  - ")
        sys.exit(1)


if __name__ == "__main__":
    main()
