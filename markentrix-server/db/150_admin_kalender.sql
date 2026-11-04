-- Admin-Kalender: eigene Termine und Sperren (blockieren die Online-Buchung der Erstgespräche)
CREATE TABLE IF NOT EXISTS kalender_eintraege (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  art text NOT NULL DEFAULT 'termin' CHECK (art IN ('termin','sperre')),
  titel text NOT NULL CHECK (length(titel) BETWEEN 1 AND 200),
  start timestamptz NOT NULL,
  ende timestamptz NOT NULL CHECK (ende > start),
  ganztag boolean NOT NULL DEFAULT false,
  notiz text,
  erstellt_von uuid,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS kalender_eintraege_start_ix ON kalender_eintraege (start);
SELECT rls_intern('kalender_eintraege');
