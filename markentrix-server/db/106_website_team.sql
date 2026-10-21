-- Leistungen (mit Dauer) und Mitarbeiter (mit eigenen Zeiten, Kalender und Urlaub) für die Terminbuchung der Kunden-Websites.
BEGIN;
CREATE TABLE IF NOT EXISTS website_leistungen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  schluessel text NOT NULL,                 -- so heißt die Leistung auf der Website (z. B. "damenschnitt")
  name text NOT NULL, beschreibung text, preis text,
  dauer_min int NOT NULL DEFAULT 30 CHECK (dauer_min BETWEEN 5 AND 720),
  puffer_min int NOT NULL DEFAULT 0 CHECK (puffer_min BETWEEN 0 AND 240),
  aktiv boolean NOT NULL DEFAULT true, sort int NOT NULL DEFAULT 0,
  UNIQUE (kunden_id, schluessel)
);
SELECT rls_intern('website_leistungen');

CREATE TABLE IF NOT EXISTS website_mitarbeiter (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  schluessel text NOT NULL, name text NOT NULL,
  aktiv boolean NOT NULL DEFAULT true, sort int NOT NULL DEFAULT 0,
  wochentage int[], von text, bis text, zeiten text,          -- leer = wie beim Betrieb
  ical_enc text, ical_geprueft_am timestamptz,                  -- eigener Kalender (verschlüsselt, nie lesbar)
  UNIQUE (kunden_id, schluessel)
);
SELECT rls_intern('website_mitarbeiter');

CREATE TABLE IF NOT EXISTS website_mitarbeiter_leistungen (
  mitarbeiter_id uuid NOT NULL REFERENCES website_mitarbeiter(id) ON DELETE CASCADE,
  leistung_id uuid NOT NULL REFERENCES website_leistungen(id) ON DELETE CASCADE,
  PRIMARY KEY (mitarbeiter_id, leistung_id)
);
SELECT rls_intern('website_mitarbeiter_leistungen');

ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS mitarbeiter_id uuid REFERENCES website_mitarbeiter(id) ON DELETE SET NULL;
ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS leistung_id uuid REFERENCES website_leistungen(id) ON DELETE SET NULL;
ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS puffer_min int NOT NULL DEFAULT 0;
DROP INDEX IF EXISTS website_termine_slot;
CREATE UNIQUE INDEX website_termine_slot ON website_termine (kunden_id, coalesce(mitarbeiter_id, '00000000-0000-0000-0000-000000000000'::uuid), start) WHERE status IN ('gebucht','reserviert');

-- Urlaub gilt für den ganzen Betrieb oder für einen Mitarbeiter
ALTER TABLE website_sperrtage ADD COLUMN IF NOT EXISTS mitarbeiter_id uuid REFERENCES website_mitarbeiter(id) ON DELETE CASCADE;
ALTER TABLE website_sperrtage DROP CONSTRAINT IF EXISTS website_sperrtage_pkey;
ALTER TABLE website_sperrtage ADD COLUMN IF NOT EXISTS id uuid DEFAULT gen_random_uuid();
UPDATE website_sperrtage SET id = gen_random_uuid() WHERE id IS NULL;
ALTER TABLE website_sperrtage ALTER COLUMN id SET NOT NULL;
ALTER TABLE website_sperrtage ADD PRIMARY KEY (id);
CREATE UNIQUE INDEX IF NOT EXISTS website_sperrtage_eindeutig ON website_sperrtage (kunden_id, tag, coalesce(mitarbeiter_id, '00000000-0000-0000-0000-000000000000'::uuid));
COMMIT;
