-- Website-Check auf markentrix.de: jede Prüfung wird gespeichert und einem Lead zugeordnet.
BEGIN;
CREATE TABLE lead_checks (
  id bigserial PRIMARY KEY,
  lead_id uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  website text,
  score int CHECK (score BETWEEN 0 AND 100),
  ergebnis jsonb NOT NULL DEFAULT '{}',
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX lead_checks_idx ON lead_checks (lead_id, erstellt_am DESC);
SELECT rls_intern('lead_checks');
COMMIT;
