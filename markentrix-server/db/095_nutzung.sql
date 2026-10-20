-- Nutzungsmessung, datensparsam: nur Seitenname je Tag und Rolle, dazu wer an einem Tag aktiv war (ohne Inhalte)
CREATE TABLE IF NOT EXISTS nutzung_seiten (
  tag    date NOT NULL,
  rolle  text NOT NULL CHECK (rolle IN ('admin','kunde','vertrieb')),
  seite  text NOT NULL CHECK (seite ~ '^[a-z0-9_-]{1,30}$'),
  n      int  NOT NULL DEFAULT 0,
  PRIMARY KEY (tag, rolle, seite)
);
CREATE TABLE IF NOT EXISTS nutzung_aktiv (
  tag         date NOT NULL,
  benutzer_id uuid NOT NULL REFERENCES benutzer(id) ON DELETE CASCADE,
  rolle       text NOT NULL,
  PRIMARY KEY (tag, benutzer_id)
);
SELECT rls_intern('nutzung_seiten');
SELECT rls_intern('nutzung_aktiv');
