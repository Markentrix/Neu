-- Fotos zu Anfragen und Terminen (Upload über die Website des Betriebs), mit Löschfrist.
-- Schalter und Frist je Betrieb: Standard aus, Frist 90 Tage (7 bis 365 einstellbar).
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS foto_aktiv boolean NOT NULL DEFAULT false;
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS foto_tage int NOT NULL DEFAULT 90;
DO $$ BEGIN
  ALTER TABLE website_dienste ADD CONSTRAINT website_dienste_foto_tage CHECK (foto_tage BETWEEN 7 AND 365);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE TABLE IF NOT EXISTS website_fotos (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  token text UNIQUE,                                        -- nur bis zur Verknüpfung; danach NULL
  anfrage_id uuid REFERENCES anfragen(id) ON DELETE CASCADE,
  buchung_id uuid REFERENCES website_termine(id) ON DELETE CASCADE,
  typ text NOT NULL CHECK (typ IN ('image/jpeg','image/png','image/webp')),
  groesse int NOT NULL,
  daten bytea NOT NULL,
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  loeschen_am timestamptz                                    -- NULL = noch nicht verknüpft (wird nach 24 Stunden entfernt)
);
CREATE INDEX IF NOT EXISTS website_fotos_kunde ON website_fotos (kunden_id);
CREATE INDEX IF NOT EXISTS website_fotos_anfrage ON website_fotos (anfrage_id) WHERE anfrage_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS website_fotos_buchung ON website_fotos (buchung_id) WHERE buchung_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS website_fotos_frist ON website_fotos (loeschen_am);
SELECT rls_kunde('website_fotos', true);
