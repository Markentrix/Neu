-- Vertriebler-Werkzeuge: Wochenziel, Angebotsanfragen aus dem Lead
ALTER TABLE vertriebspartner ADD COLUMN IF NOT EXISTS wochenziel_anrufe int NOT NULL DEFAULT 40 CHECK (wochenziel_anrufe BETWEEN 1 AND 500);

CREATE TABLE IF NOT EXISTS angebotsanfragen (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id             uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  vertriebspartner_id uuid REFERENCES vertriebspartner(id) ON DELETE SET NULL,
  paket_code          text,
  notiz               text,
  status              text NOT NULL DEFAULT 'angefragt' CHECK (status IN ('angefragt','in_pruefung','angebot_raus','angenommen','abgelehnt')),
  admin_notiz         text,
  erstellt_am         timestamptz NOT NULL DEFAULT now(),
  geaendert_am        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS angebotsanfragen_lead_idx ON angebotsanfragen (lead_id);
CREATE INDEX IF NOT EXISTS angebotsanfragen_partner_idx ON angebotsanfragen (vertriebspartner_id, erstellt_am DESC);
SELECT rls_intern('angebotsanfragen');
