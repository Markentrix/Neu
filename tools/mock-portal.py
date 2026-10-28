# Testserver: liefert website-fertig/ aus und simuliert die Portal-API (nur für die Prüfung, nicht Teil der Abgabe)
import json, sys, datetime
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import os
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "website-fertig")
MODE = sys.argv[1] if len(sys.argv)>1 else "ok"   # ok | down
class H(SimpleHTTPRequestHandler):
    def __init__(s,*a,**k): super().__init__(*a,directory=ROOT,**k)
    def log_message(s,*a): pass
    def _json(s,code,obj):
        b=json.dumps(obj).encode(); s.send_response(code); s.send_header("Content-Type","application/json"); s.send_header("Content-Length",str(len(b))); s.end_headers(); s.wfile.write(b)
    def do_GET(s):
        u=urlparse(s.path)
        if u.path.startswith("/api/"):
            if MODE=="down": s.send_response(503); s.end_headers(); return
            if u.path=="/api/verfuegbarkeit":
                return s._json(200,{"blocked":[(datetime.date.today()+datetime.timedelta(days=2)).isoformat()],"closedWeekdays":[],"nextFree":(datetime.date.today()+datetime.timedelta(days=1)).isoformat(),"selfBooking":True,"slotTimes":["13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00"]})
            if u.path=="/api/slots":
                tag=parse_qs(u.query).get("tag",[""])[0]
                return s._json(200,{"tag":tag,"slots":[{"zeit":t,"frei":t!="15:00"} for t in ["10:00","13:00","14:00","15:00","16:00","17:00","18:00","19:00","20:00"]]})
            return s._json(404,{"ok":False})
        if u.path=="/": s.path="/index.html"
        return super().do_GET()
    def do_POST(s):
        n=int(s.headers.get("Content-Length",0)); body=json.loads(s.rfile.read(n) or b"{}")
        if s.path=="/api/e": s.send_response(204); s.end_headers(); return
        if MODE=="down": s.send_response(503); s.end_headers(); return
        if s.path=="/api/anfrage":
            if body.get("website"): return s._json(422,{"ok":False,"errors":{"name":"Spam"}})
            if not body.get("einwilligung")=="ja" or not body.get("name") or not body.get("email"): return s._json(422,{"ok":False,"errors":{"email":"Bitte E-Mail angeben","name":"Bitte Namen angeben"}})
            if body.get("typ")=="termin" and body.get("uhrzeit")=="16:00": return s._json(422,{"ok":False,"errors":{"uhrzeit":"Zeit gerade vergeben"}})
            print("ANFRAGE", json.dumps(body, ensure_ascii=False)[:400], flush=True)
            return s._json(200,{"ok":True,"ref":"BK-2026-0042"})
        s.send_response(404); s.end_headers()
port=int(sys.argv[2]) if len(sys.argv)>2 else 8765
HTTPServer(("127.0.0.1",port),H).serve_forever()
