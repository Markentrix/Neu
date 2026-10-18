-- 016 Standard-Module je Produkt: was ein neuer Kunde mit einem Paket automatisch freigeschaltet bekommt.
-- Im Admin-Bereich pro Kunde jederzeit änderbar.
BEGIN;
INSERT INTO produkt_module (produkt_code, modul_code)
SELECT p.code, m.code FROM produkte p CROSS JOIN module m
WHERE m.code IN ('einstellungen','kontakte_angebote_vertraege') ON CONFLICT DO NOTHING;

INSERT INTO produkt_module (produkt_code, modul_code)
SELECT p.code, m.code FROM produkte p CROSS JOIN module m
WHERE p.kategorie = 'ki' AND m.code IN ('ki_chat','anfragen_termine','automationen') ON CONFLICT DO NOTHING;

INSERT INTO produkt_module (produkt_code, modul_code)
SELECT p.code, 'website' FROM produkte p WHERE p.kategorie = 'website' ON CONFLICT DO NOTHING;

INSERT INTO produkt_module (produkt_code, modul_code)
SELECT p.code, 'werbung_berichte' FROM produkte p WHERE p.kategorie IN ('sichtbarkeit','lead') ON CONFLICT DO NOTHING;
-- Wochenangebote-Upload wird bewusst nur pro Kunde von Hand freigeschaltet.
COMMIT;
