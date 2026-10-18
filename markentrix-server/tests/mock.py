import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n=int(self.headers.get("content-length",0)); b=json.loads(self.rfile.read(n))
        open("/var/tmp/pt/mock_last.json","w").write(json.dumps({"headers":dict(self.headers),"body":b}))
        if self.headers.get("x-api-key")!="sk-test": self.send_response(401); self.end_headers(); self.wfile.write(b"{}"); return
        out=json.dumps({"content":[{"type":"text","text":"Hallo! Du hast 1 neue Anfrage."}],"usage":{"input_tokens":321,"output_tokens":45}}).encode()
        self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(out)
    def log_message(self,*a): pass
HTTPServer(("127.0.0.1",8999),H).serve_forever()
