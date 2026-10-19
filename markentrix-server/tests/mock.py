import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n=int(self.headers.get("content-length",0)); b=json.loads(self.rfile.read(n))
        open("/var/tmp/pt/mock_last.json","w").write(json.dumps({"headers":dict(self.headers),"body":b}))
        if self.headers.get("x-api-key")!="sk-test": self.send_response(401); self.end_headers(); self.wfile.write(b"{}"); return
        if "Übersetzer" in str(b.get("system","")):
            import re as _re
            daten=json.loads(_re.search(r"<daten>\n(.*)\n</daten>",b["messages"][0]["content"],_re.S).group(1))
            res={f:{sp:f"[{sp}] {t}" for sp in daten["zielsprachen"]} for f,t in daten["felder"].items()}
            if "kaputt" in json.dumps(daten): res="das ist kein JSON"
            out=json.dumps({"content":[{"type":"text","text":"Hier: "+(res if isinstance(res,str) else json.dumps(res,ensure_ascii=False))}],"usage":{"input_tokens":100,"output_tokens":50}}).encode()
            self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(out); return
        if "Berichts-Assistent" in str(b.get("system","")):
            out=json.dumps({"content":[{"type":"text","text":"Hier: "+json.dumps({"einordnung":"Entwurf der KI: solide Entwicklung.","schritte":["Erster KI-Schritt","Zweiter KI-Schritt"]},ensure_ascii=False)}],"usage":{"input_tokens":50,"output_tokens":30}}).encode()
            self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(out); return
        out=json.dumps({"content":[{"type":"text","text":"Hallo! Du hast 1 neue Anfrage."}],"usage":{"input_tokens":321,"output_tokens":45}}).encode()
        self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(out)
    def log_message(self,*a): pass
HTTPServer(("127.0.0.1",8999),H).serve_forever()
