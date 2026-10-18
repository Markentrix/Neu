-- Mehrere Benutzer pro Kunde mit Rollen, Branding (Logo, Farbe)
ALTER TABLE benutzer ADD COLUMN IF NOT EXISTS kunden_rolle text NOT NULL DEFAULT 'inhaber';
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'benutzer_kunden_rolle_check') THEN
    ALTER TABLE benutzer ADD CONSTRAINT benutzer_kunden_rolle_check CHECK (kunden_rolle IN ('inhaber','mitarbeiter','nur_lesen'));
  END IF;
END $$;
ALTER TABLE kunden ADD COLUMN IF NOT EXISTS branding_farbe text CHECK (branding_farbe IS NULL OR branding_farbe ~ '^#[0-9a-fA-F]{6}$');
ALTER TABLE kunden ADD COLUMN IF NOT EXISTS logo bytea;
ALTER TABLE kunden ADD COLUMN IF NOT EXISTS logo_typ text;
