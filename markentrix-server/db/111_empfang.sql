-- Rolle „Empfang“ (nur Anfragen, Termine, Nachrichten) und befristete Zugänge für Vertretungen
BEGIN;
ALTER TABLE benutzer DROP CONSTRAINT IF EXISTS benutzer_kunden_rolle_check;
ALTER TABLE benutzer ADD CONSTRAINT benutzer_kunden_rolle_check CHECK (kunden_rolle IN ('inhaber','mitarbeiter','nur_lesen','empfang'));
ALTER TABLE benutzer ADD COLUMN IF NOT EXISTS zugang_bis date;
COMMIT;
