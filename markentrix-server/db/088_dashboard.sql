-- Dashboard: Ansicht je Benutzer, Benachrichtigungen (Glocke), Kündigungsdatum
ALTER TABLE benutzer ADD COLUMN IF NOT EXISTS ansicht jsonb NOT NULL DEFAULT '{}'::jsonb;

CREATE TABLE IF NOT EXISTS benachrichtigungen (
  id bigserial PRIMARY KEY,
  benutzer_id uuid NOT NULL REFERENCES benutzer(id) ON DELETE CASCADE,
  tag text, titel text NOT NULL, text text, url text,
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  gelesen_am timestamptz
);
CREATE INDEX IF NOT EXISTS benachrichtigungen_idx ON benachrichtigungen (benutzer_id, erstellt_am DESC);
SELECT rls_intern('benachrichtigungen');

ALTER TABLE kunden ADD COLUMN IF NOT EXISTS gekuendigt_am timestamptz;
UPDATE kunden SET gekuendigt_am = geaendert_am WHERE status IN ('gekuendigt','beendet') AND gekuendigt_am IS NULL;
CREATE OR REPLACE FUNCTION kunden_kuendigung() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.status IN ('gekuendigt','beendet') THEN
    IF NEW.gekuendigt_am IS NULL THEN NEW.gekuendigt_am := now(); END IF;
  ELSE
    NEW.gekuendigt_am := NULL;
  END IF;
  RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS kunden_kuendigung ON kunden;
CREATE TRIGGER kunden_kuendigung BEFORE UPDATE OF status ON kunden FOR EACH ROW EXECUTE FUNCTION kunden_kuendigung();
