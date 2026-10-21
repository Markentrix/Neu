-- Kündigung per Portal: verbindlich, mit berechnetem Vertragsende
BEGIN;
ALTER TABLE kuendigungswuensche ADD COLUMN IF NOT EXISTS ende_am date;
ALTER TABLE kuendigungswuensche ADD COLUMN IF NOT EXISTS vollzogen_am timestamptz;
ALTER TABLE kuendigungswuensche ADD COLUMN IF NOT EXISTS ip text;
COMMIT;
