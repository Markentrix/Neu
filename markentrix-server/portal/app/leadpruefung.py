"""Prüfungen beim Anlegen von Leads: Sperrliste und Dubletten (andere Leads, Kunden)."""

from fastapi import HTTPException

from . import sperre


def dublette(cur, email=None, telefon=None, firma=None, plz=None, ausser=None) -> dict | None:
    """Findet einen vorhandenen Lead oder Kunden mit derselben E-Mail, Telefonnummer oder Firma+PLZ."""
    m = sperre.mail(email)
    t = sperre.telefon(telefon)
    f = (firma or "").strip().lower()
    cur.execute("""SELECT 'lead' AS art, id, firma, vertriebspartner_id FROM leads
                   WHERE (%(ausser)s::uuid IS NULL OR id <> %(ausser)s::uuid)
                     AND ((%(m)s::text IS NOT NULL AND lower(email) = %(m)s)
                       OR (%(t)s::text IS NOT NULL AND regexp_replace(coalesce(telefon,''),'[^0-9]','','g') <> '' AND
                           CASE WHEN regexp_replace(telefon,'[^0-9]','','g') LIKE '00%%' THEN substr(regexp_replace(telefon,'[^0-9]','','g'),3)
                                WHEN regexp_replace(telefon,'[^0-9]','','g') LIKE '0%%' THEN '49' || substr(regexp_replace(telefon,'[^0-9]','','g'),2)
                                ELSE regexp_replace(telefon,'[^0-9]','','g') END = %(t)s)
                       OR (%(f)s <> '' AND lower(firma) = %(f)s AND coalesce(plz,'') = coalesce(%(plz)s,''))) LIMIT 1""",
                {"m": m, "t": t, "f": f, "plz": plz, "ausser": ausser})
    r = cur.fetchone()
    if r:
        return r
    cur.execute("""SELECT 'kunde' AS art, id, firma, vertriebspartner_id FROM kunden
                   WHERE (%(m)s::text IS NOT NULL AND lower(email) = %(m)s) OR (%(f)s <> '' AND lower(firma) = %(f)s AND coalesce(plz,'') = coalesce(%(plz)s,'')) LIMIT 1""",
                {"m": m, "f": f, "plz": plz})
    return cur.fetchone()


def pruefen(cur, d: dict, eigener_partner=None, trotzdem: bool = False) -> None:
    """Wirft 409, wenn der Lead gesperrt ist oder schon existiert. `eigener_partner`: Vertriebler-Sicht (keine Namen fremder Vertriebler)."""
    s = sperre.treffer(cur, d.get("email"), d.get("telefon"), d.get("website"))
    if s:
        grund = {"widerspruch": "hat widersprochen", "abmeldung": "hat sich abgemeldet", "kein_interesse": "hat kein Interesse geäußert"}.get(s["grund"], "steht auf der Sperrliste")
        raise HTTPException(409, f"Dieser Kontakt {grund} und darf nicht erneut angesprochen werden.")
    if trotzdem:
        return
    x = dublette(cur, d.get("email"), d.get("telefon"), d.get("firma"), d.get("plz"))
    if x:
        if x["art"] == "kunde":
            raise HTTPException(409, f"„{x['firma']}“ ist bereits Kunde bei Markentrix.")
        if eigener_partner is not None:
            if str(x["vertriebspartner_id"] or "") == str(eigener_partner):
                raise HTTPException(409, f"„{x['firma']}“ ist schon in deiner Liste.")
            raise HTTPException(409, f"„{x['firma']}“ ist bei Markentrix bereits erfasst. Bitte sprich kurz mit dem Team, bevor du den Kontakt ansprichst.")
        raise HTTPException(409, f"„{x['firma']}“ gibt es schon als Lead. Zum Anlegen trotzdem „Trotzdem anlegen“ wählen.")
