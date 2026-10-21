-- DNS-Anleitung an den Kunden: wann gesendet, wann erinnert
BEGIN;
ALTER TABLE domain_pruefung ADD COLUMN IF NOT EXISTS kundenmail_am timestamptz;
ALTER TABLE domain_pruefung ADD COLUMN IF NOT EXISTS erinnert_am timestamptz;
ALTER TABLE domain_pruefung ADD COLUMN IF NOT EXISTS erinnerungen integer NOT NULL DEFAULT 0;
COMMIT;
