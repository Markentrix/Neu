-- Verträge: Erinnerungen, Online-Bestätigung im Portal (einfache elektronische Signatur mit Protokoll), Widerruf, Einarbeitung der Vertriebler
BEGIN;
ALTER TABLE vertragsdokumente ADD COLUMN IF NOT EXISTS erinnert_am timestamptz;
ALTER TABLE vertragsdokumente ADD COLUMN IF NOT EXISTS erinnerungen int NOT NULL DEFAULT 0;
ALTER TABLE vertragsdokumente ADD COLUMN IF NOT EXISTS online_am timestamptz;
ALTER TABLE vertragsdokumente ADD COLUMN IF NOT EXISTS online_name text;
ALTER TABLE vertragsdokumente ADD COLUMN IF NOT EXISTS online_email text;
ALTER TABLE vertragsdokumente ADD COLUMN IF NOT EXISTS online_ip text;
ALTER TABLE vertragsdokumente ADD COLUMN IF NOT EXISTS online_hash text;
ALTER TABLE vertragsdokumente ADD COLUMN IF NOT EXISTS antworten jsonb;
ALTER TABLE vertragsdokumente ADD COLUMN IF NOT EXISTS widerrufen_am timestamptz;
ALTER TABLE vertriebspartner ADD COLUMN IF NOT EXISTS leitfaden_gelesen_am timestamptz;
COMMIT;
