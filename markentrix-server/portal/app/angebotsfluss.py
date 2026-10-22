"""Annahme eines Angebots – egal ob online über den Link oder telefonisch vom Team erfasst: gleicher Ablauf (Verlauf, Aufgabe, Hinweise, Bestätigung an den Kunden)."""
from . import config, mailer, push
from .routes_zusammenarbeit import admin_empfaenger
from .security import audit


def angenommen(cur, b: dict, name: str, kanal: str, von: str, ip: str | None = None, user: dict | None = None) -> dict:
    """`b`: Beleg (mit lead_id, nummer, empfaenger). Setzt den Beleg auf angenommen und bereitet Folgeschritte vor. Gibt Infos für `melden` zurück."""
    cur.execute("UPDATE belege SET status='angenommen', angenommen_am=now(), angenommen_von=%s, geaendert_am=now() WHERE id=%s", (name, b["id"]))
    info = {"nummer": b["nummer"], "name": name, "kanal": kanal, "lead_id": b.get("lead_id"), "firma": b.get("lead_firma") or (b.get("empfaenger") or {}).get("firma") or "", "ids": [], "an_admin": None, "an_kunde": None}
    if b.get("lead_id"):
        lid = b["lead_id"]
        cur.execute("INSERT INTO lead_aktivitaeten (lead_id, art, inhalt, von) VALUES (%s,'statuswechsel',%s,%s)",
                    (lid, f"Angebot {b['nummer']} {'online' if kanal == 'online' else 'telefonisch/schriftlich'} angenommen von {name}", von))
        cur.execute("UPDATE angebotsanfragen SET status='angenommen', geaendert_am=now() WHERE lead_id=%s AND status IN ('angefragt','in_pruefung','angebot_raus')", (lid,))
        cur.execute("UPDATE leads SET wiedervorlage_am=current_date, letzter_kontakt_am=now() WHERE id=%s", (lid,))
        cur.execute("INSERT INTO aufgaben (titel, beschreibung, faellig_am) VALUES (%s,%s,current_date)",
                    (f"Angebot angenommen: Kunde anlegen ({info['firma']})"[:200], f"{name} hat Angebot {b['nummer']} angenommen. Im Lead „In Kunden umwandeln“ wählen (Assistent legt Paket und Buchung an), dann Onboarding starten."))
        cur.execute("SELECT vertriebspartner_id, email, ansprechpartner FROM leads WHERE id=%s", (lid,))
        l = cur.fetchone()
        info["ids"] = push.admins(cur) + (push.partner(cur, l["vertriebspartner_id"]) if l and l["vertriebspartner_id"] else [])
        info["an_kunde"] = ((b.get("empfaenger") or {}).get("email") or (l and l["email"]) or "").strip() or None
    audit(cur, user, "lead_angebot_angenommen", None, {"lead": str(b.get("lead_id")), "nummer": b["nummer"], "name": name, "kanal": kanal, "ip": ip})
    info["an_admin"] = admin_empfaenger(cur)
    return info


def melden(info: dict) -> None:
    """Nach dem Commit: Push ans Team und den Vertriebler, Mail ans Team, Bestätigung an den Kunden."""
    link = f"{config.BASE_URL}/admin#lead/{info['lead_id']}" if info["lead_id"] else config.BASE_URL + "/admin"
    push.senden(info["ids"], "Angebot angenommen 🎉", f"{info['firma']} hat {info['nummer']} angenommen.", "/admin#lead/" + str(info["lead_id"]), "angebotsreaktion")
    if info["an_admin"]:
        mailer.senden(info["an_admin"], f"Angebot {info['nummer']} wurde angenommen", f"{info['name']} ({info['firma']}) hat das Angebot {info['nummer']} angenommen ({'online' if info['kanal'] == 'online' else 'vom Team erfasst'}).\n\nNächster Schritt: Im Lead „In Kunden umwandeln“ wählen.\n{link}" + mailer.SIGNATUR)
    if info["an_kunde"]:
        mailer.angebot_bestaetigung(info["an_kunde"], info["name"], info["nummer"])
