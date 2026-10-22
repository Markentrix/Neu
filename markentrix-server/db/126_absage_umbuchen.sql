-- Absageregel (kostenlos bis X Stunden vorher), Erstattungen, Quittung, Fragen je Leistung.
BEGIN;
ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS abgesagt_am timestamptz;
ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS abgesagt_von text;            -- besucher | betrieb
ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS storno_kostenlos boolean;
ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS erstattet_am timestamptz;
ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS quittung_am timestamptz;
ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS verschoben_am timestamptz;
ALTER TABLE website_leistungen ADD COLUMN IF NOT EXISTS felder jsonb NOT NULL DEFAULT '[]'::jsonb;   -- Fragen an den Besucher: [{"key","label","pflicht"}]
COMMIT;
