-- Briefing-Fragebogen der Kunden und extern gepflegte Monatszahlen (Besucher, Google).
BEGIN;

CREATE TABLE briefings (
  kunden_id uuid PRIMARY KEY REFERENCES kunden(id) ON DELETE CASCADE,
  daten jsonb NOT NULL DEFAULT '{}',
  status text NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','abgeschickt')),
  abgeschickt_am timestamptz,
  geaendert_von uuid,
  geaendert_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_kunde('briefings', true);

CREATE TABLE kennzahlen_extern (
  id bigserial PRIMARY KEY,
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  monat date NOT NULL,
  besucher int CHECK (besucher >= 0),
  google_aufrufe int CHECK (google_aufrufe >= 0),
  google_bewertungen int CHECK (google_bewertungen >= 0),
  google_sterne numeric(2,1) CHECK (google_sterne BETWEEN 1 AND 5),
  UNIQUE (kunden_id, monat)
);
SELECT rls_kunde('kennzahlen_extern', false);

COMMIT;
