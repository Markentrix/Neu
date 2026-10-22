-- Öffentliche Statusseite der Plattform: Störungs-, Wartungs- und Infomeldungen
BEGIN;
CREATE TABLE IF NOT EXISTS statusmeldungen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  art text NOT NULL CHECK (art IN ('stoerung','wartung','info')),
  titel text NOT NULL CHECK (length(titel) BETWEEN 1 AND 120),
  text text NOT NULL DEFAULT '' CHECK (length(text) <= 1500),
  beginn timestamptz NOT NULL DEFAULT now(),
  beendet_am timestamptz,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS statusmeldungen_idx ON statusmeldungen (erstellt_am DESC);
SELECT rls_intern('statusmeldungen');
COMMIT;
