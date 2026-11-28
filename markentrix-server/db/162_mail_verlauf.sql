-- 162 Mail-Verlauf je Kunde und Lead: welche Mail wann an wen ging (Betreff, Art, zugestellt oder fehlgeschlagen).
-- Anders als mail_protokoll (nur Domain, 90 Tage) gehört dieser Verlauf zur Kundenakte, damit das Büro sieht, wie oft ein Kunde schon erinnert wurde.
BEGIN;
CREATE TABLE IF NOT EXISTS mail_verlauf (
  id          bigserial PRIMARY KEY,
  zeit        timestamptz NOT NULL DEFAULT now(),
  kunden_id   uuid REFERENCES kunden(id) ON DELETE CASCADE,
  lead_id     uuid REFERENCES leads(id) ON DELETE CASCADE,
  art         text NOT NULL DEFAULT 'system',
  betreff     text,
  an          text,
  ok          boolean NOT NULL,
  fehler      text,
  CHECK (kunden_id IS NOT NULL OR lead_id IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS mail_verlauf_kunde_idx ON mail_verlauf (kunden_id, zeit DESC) WHERE kunden_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS mail_verlauf_lead_idx ON mail_verlauf (lead_id, zeit DESC) WHERE lead_id IS NOT NULL;
SELECT rls_intern('mail_verlauf');
COMMIT;
