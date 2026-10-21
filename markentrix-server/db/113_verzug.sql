-- Zahlungsverzug: Wartungspläne und Website-Dienste können vorübergehend pausiert werden
BEGIN;
ALTER TABLE abrechnungsplaene ADD COLUMN IF NOT EXISTS pausiert_verzug boolean NOT NULL DEFAULT false;
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS verzug_pause boolean NOT NULL DEFAULT false;
COMMIT;
