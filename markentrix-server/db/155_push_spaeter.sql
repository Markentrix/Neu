-- Push-Meldung „In 1 Stunde erinnern“: die Meldung kommt später noch einmal
CREATE TABLE IF NOT EXISTS push_spaeter (
  id bigserial PRIMARY KEY,
  benutzer_id uuid NOT NULL REFERENCES benutzer(id) ON DELETE CASCADE,
  titel text NOT NULL,
  text text NOT NULL DEFAULT '',
  url text NOT NULL DEFAULT '/',
  faellig_am timestamptz NOT NULL,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS push_spaeter_faellig_idx ON push_spaeter (faellig_am);
SELECT rls_intern('push_spaeter');
