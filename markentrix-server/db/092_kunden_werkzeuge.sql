-- Kunden-Werkzeuge: Heute-Seite, Anfragen-Inbox mit Antwortvorlagen, Bewertungsbitten mit Freigabe
ALTER TABLE anfragen ADD COLUMN IF NOT EXISTS antwort_am timestamptz;
ALTER TABLE anfragen ADD COLUMN IF NOT EXISTS antwort_kanal text;

CREATE TABLE IF NOT EXISTS kunden_werkzeuge (
  kunden_id uuid PRIMARY KEY REFERENCES kunden(id) ON DELETE CASCADE,
  bewertungslink text, bewertungstext text
);
SELECT rls_kunde('kunden_werkzeuge', true);

CREATE TABLE IF NOT EXISTS antwortvorlagen_kunde (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  name text NOT NULL, text text NOT NULL, erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS antwortvorlagen_kunde_idx ON antwortvorlagen_kunde (kunden_id);
SELECT rls_kunde('antwortvorlagen_kunde', true);

-- Bewertungsbitten: der Kunde legt Entwürfe an und gibt selbst frei; das Portal versendet nichts.
ALTER TABLE bewertungsanfragen ADD COLUMN IF NOT EXISTS name text;
ALTER TABLE bewertungsanfragen ADD COLUMN IF NOT EXISTS kanal text;
ALTER TABLE bewertungsanfragen ADD COLUMN IF NOT EXISTS text text;
DROP POLICY IF EXISTS lesen ON bewertungsanfragen;
DROP POLICY IF EXISTS intern_schreiben ON bewertungsanfragen;
DROP POLICY IF EXISTS trennung ON bewertungsanfragen;
CREATE POLICY trennung ON bewertungsanfragen USING (app_intern() OR kunden_id = app_kunden_id()) WITH CHECK (app_intern() OR kunden_id = app_kunden_id());
