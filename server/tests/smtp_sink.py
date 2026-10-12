#!/usr/bin/env python3
"""Kleiner Test-Mailserver für die Formulartests: STARTTLS, AUTH, nimmt Nachrichten entgegen und merkt sie sich.

Nur für Tests gedacht. Er verschickt nichts.
"""
import base64
import os
import socket
import ssl
import subprocess
import tempfile
import threading


class Sink:
    def __init__(self, user="anfragen@psschneider.de", password="geheim", port=0, fail_data=False, dump_dir=None):
        self.user, self.password = user, password
        self.dump_dir = dump_dir      # wenn gesetzt: jede Nachricht als Datei ablegen; Datei FAIL dort lässt DATA scheitern
        self.messages = []          # jede Nachricht: dict(from_, to, raw)
        self.auth_failures = 0
        self.fail_data = fail_data
        self._dir = tempfile.mkdtemp(prefix="sink-")
        key, crt = os.path.join(self._dir, "k.pem"), os.path.join(self._dir, "c.pem")
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", crt,
                        "-days", "2", "-subj", "/CN=127.0.0.1"], check=True, capture_output=True)
        self.ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.ctx.load_cert_chain(crt, key)
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", port))
        self.sock.listen(8)
        self.port = self.sock.getsockname()[1]
        self._stop = False
        threading.Thread(target=self._serve, daemon=True).start()

    def close(self):
        self._stop = True
        try:
            self.sock.close()
        except OSError:
            pass

    def _serve(self):
        while not self._stop:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn):
        conn.settimeout(15)
        buf = b""

        def send(text):
            conn.sendall(text.encode() + b"\r\n")

        def readline():
            nonlocal buf
            while b"\r\n" not in buf:
                chunk = conn.recv(65536)
                if not chunk:
                    return None
                buf += chunk
            line, buf = buf.split(b"\r\n", 1)
            return line.decode(errors="replace")

        tls, authed = False, False
        mail_from, rcpt = "", []
        try:
            send("220 sink ESMTP")
            while True:
                line = readline()
                if line is None:
                    return
                cmd = line.upper()
                if cmd.startswith("EHLO"):
                    send("250-sink")
                    if not tls:
                        send("250-STARTTLS")
                    send("250-AUTH PLAIN LOGIN")
                    send("250 8BITMIME")
                elif cmd == "STARTTLS":
                    send("220 weiter")
                    conn = self.ctx.wrap_socket(conn, server_side=True)
                    conn.settimeout(15)
                    tls, buf = True, b""
                elif cmd.startswith("AUTH PLAIN"):
                    parts = base64.b64decode(line.split(" ", 2)[2]).split(b"\0")
                    authed = parts[1].decode() == self.user and parts[2].decode() == self.password
                    if authed:
                        send("235 ok")
                    else:
                        self.auth_failures += 1
                        send("535 falsche Zugangsdaten")
                elif cmd == "AUTH LOGIN":
                    send("334 VXNlcm5hbWU6")
                    u = base64.b64decode(readline() or "").decode()
                    send("334 UGFzc3dvcmQ6")
                    p = base64.b64decode(readline() or "").decode()
                    authed = (u, p) == (self.user, self.password)
                    send("235 ok" if authed else "535 falsche Zugangsdaten")
                    if not authed:
                        self.auth_failures += 1
                elif cmd.startswith("MAIL FROM"):
                    if not tls or not authed:
                        send("530 STARTTLS und Anmeldung erforderlich")
                        continue
                    mail_from = line[line.index("<") + 1:line.index(">")]
                    send("250 ok")
                elif cmd.startswith("RCPT TO"):
                    rcpt.append(line[line.index("<") + 1:line.index(">")])
                    send("250 ok")
                elif cmd == "DATA":
                    if self.fail_data or (self.dump_dir and os.path.exists(os.path.join(self.dump_dir, "FAIL"))):
                        send("554 abgelehnt")
                        continue
                    send("354 los")
                    data = b""
                    while True:
                        while b"\r\n.\r\n" not in buf:
                            chunk = conn.recv(65536)
                            if not chunk:
                                return
                            buf += chunk
                        data, buf = buf.split(b"\r\n.\r\n", 1)
                        break
                    raw = data.replace(b"\r\n..", b"\r\n.")
                    self.messages.append({"from_": mail_from, "to": list(rcpt), "raw": raw})
                    if self.dump_dir:
                        with open(os.path.join(self.dump_dir, f"mail-{len(self.messages):03d}.eml"), "wb") as fh:
                            fh.write(raw)
                    send("250 angenommen")
                elif cmd == "QUIT":
                    send("221 tschüss")
                    return
                elif cmd == "RSET":
                    send("250 ok")
                else:
                    send("502 unbekannt")
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--port", type=int, default=2525)
    ap.add_argument("--dump", help="Ordner, in dem Nachrichten als .eml abgelegt werden")
    a = ap.parse_args()
    if a.dump:
        os.makedirs(a.dump, exist_ok=True)
    s = Sink(port=a.port, dump_dir=a.dump)
    print(f"Test-Mailserver läuft auf 127.0.0.1:{a.port}, Strg+C beendet", flush=True)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass
