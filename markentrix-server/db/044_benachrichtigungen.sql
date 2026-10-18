-- Benachrichtigungen, Monatsberichte
ALTER TABLE kunden ADD COLUMN IF NOT EXISTS benachr_email text;                        -- optional andere Adresse als die Kontakt-E-Mail
ALTER TABLE kunden ADD COLUMN IF NOT EXISTS benachr_anfragen boolean NOT NULL DEFAULT true;
ALTER TABLE kunden ADD COLUMN IF NOT EXISTS benachr_termine boolean NOT NULL DEFAULT true;
ALTER TABLE kunden ADD COLUMN IF NOT EXISTS benachr_bericht boolean NOT NULL DEFAULT true;

ALTER TABLE anfragen ADD COLUMN IF NOT EXISTS benachrichtigt boolean;
UPDATE anfragen SET benachrichtigt = true WHERE benachrichtigt IS NULL;               -- Altbestand nicht nachträglich melden
ALTER TABLE anfragen ALTER COLUMN benachrichtigt SET DEFAULT false;
ALTER TABLE anfragen ALTER COLUMN benachrichtigt SET NOT NULL;
CREATE INDEX IF NOT EXISTS anfragen_offen_idx ON anfragen (erstellt_am) WHERE NOT benachrichtigt;

-- (workflow_fehler: siehe 071_workflow_fehler_benachrichtigung.sql, die Tabelle entsteht erst in 070)

ALTER TABLE berichte ADD COLUMN IF NOT EXISTS versendet_am timestamptz;
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'berichte_art_check') THEN
    ALTER TABLE berichte DROP CONSTRAINT berichte_art_check;
  END IF;
  ALTER TABLE berichte ADD CONSTRAINT berichte_art_check CHECK (art IN ('werbung','website','social','lokale_sichtbarkeit','sonstiges','monatsbericht'));
END $$;
CREATE UNIQUE INDEX IF NOT EXISTS berichte_monat_uq ON berichte (kunden_id, zeitraum_von) WHERE art = 'monatsbericht';
