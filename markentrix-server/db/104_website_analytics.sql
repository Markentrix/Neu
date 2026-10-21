-- Google Analytics der Kunden-Websites: nur die öffentliche Mess-ID, geladen erst nach Einwilligung des Besuchers.
BEGIN;
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS ga_aktiv boolean NOT NULL DEFAULT false;
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS ga_id text;
COMMIT;
