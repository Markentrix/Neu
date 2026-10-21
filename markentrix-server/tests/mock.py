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
        if "Gesprächs-Assistent" in str(b.get("system","")):
            out=json.dumps({"content":[{"type":"text","text":"Hier: "+json.dumps({"einstieg":"Guten Tag, hier ist Markentrix.","fragen":["Wie kommen Kunden zu Ihnen?","Wer beantwortet Anfragen?","Haben Sie eine Website?"],"nutzen":"Wir können Anfragen automatisch bearbeiten.","einwaende":[{"einwand":"Keine Zeit","antwort":"Ich fasse mich kurz."},{"einwand":"Zu teuer","antwort":"Wir sprechen erst über Ihren Bedarf."},{"einwand":"Haben wir schon","antwort":"Gern ergänzend."}],"abschluss":"Darf ich einen kurzen Termin vorschlagen?"},ensure_ascii=False)}],"usage":{"input_tokens":50,"output_tokens":30}}).encode()
            self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(out); return
        if "Berichts-Assistent" in str(b.get("system","")):
            out=json.dumps({"content":[{"type":"text","text":"Hier: "+json.dumps({"einordnung":"Entwurf der KI: solide Entwicklung.","schritte":["Erster KI-Schritt","Zweiter KI-Schritt"]},ensure_ascii=False)}],"usage":{"input_tokens":50,"output_tokens":30}}).encode()
            self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(out); return
        out=json.dumps({"content":[{"type":"text","text":"Hallo! Du hast 1 neue Anfrage."}],"usage":{"input_tokens":321,"output_tokens":45}}).encode()
        self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(out)
    def do_GET(self):
        import datetime as _d
        if self.path.startswith("/v1/places/"):
            if self.headers.get("x-goog-api-key")!="places-test": self.send_response(403); self.end_headers(); self.wfile.write(b"{}"); return
            if "NichtDa" in self.path: self.send_response(404); self.end_headers(); self.wfile.write(b"{}"); return
            out=json.dumps({"rating":4.7,"userRatingCount":128,"googleMapsUri":"https://maps.google.com/?cid=1","reviews":[{"rating":5,"text":{"text":"Sehr gut! <b>Top</b>"},"authorAttribution":{"displayName":"Anna K."},"relativePublishTimeDescription":"vor 2 Wochen"},{"rating":4,"text":{"text":"Freundlich."},"authorAttribution":{"displayName":"Ben"}}]}).encode()
            self.send_response(200); self.send_header("content-type","application/json"); self.end_headers(); self.wfile.write(out); return
        if self.path.startswith("/ical/"):
            if "leer" in self.path: self.send_response(200); self.end_headers(); self.wfile.write(b"hallo"); return
            if "weg" in self.path: self.send_response(404); self.end_headers(); self.wfile.write(b""); return
            h=_d.date.today(); f=lambda n:(h+_d.timedelta(days=n)).strftime("%Y%m%d")
            ics="\r\n".join(["BEGIN:VCALENDAR","VERSION:2.0",
              "BEGIN:VEVENT","UID:a1","DTSTART;TZID=Europe/Berlin:"+f(2)+"T100000","DTEND;TZID=Europe/Berlin:"+f(2)+"T110000","SUMMARY:Einzeltermin","END:VEVENT",
              "BEGIN:VEVENT","UID:a2","DTSTART;TZID=Europe/Berlin:"+f(-30)+"T120000","DTEND;TZID=Europe/Berlin:"+f(-30)+"T130000","RRULE:FREQ=DAILY;INTERVAL=1","SUMMARY:Mittag taeglich","END:VEVENT",
              "BEGIN:VEVENT","UID:a3","DTSTART;VALUE=DATE:"+f(4),"DTEND;VALUE=DATE:"+f(5),"SUMMARY:Urlaub","END:VEVENT",
              "BEGIN:VEVENT","UID:a4","DTSTART:"+f(3)+"T080000Z","DTEND:"+f(3)+"T090000Z","TRANSP:TRANSPARENT","SUMMARY:Frei","END:VEVENT",
              "END:VCALENDAR",""])
            self.send_response(200); self.send_header("content-type","text/calendar"); self.end_headers(); self.wfile.write(ics.encode()); return
        self.send_response(404); self.end_headers()
    def log_message(self,*a): pass
HTTPServer(("127.0.0.1",8999),H).serve_forever()
