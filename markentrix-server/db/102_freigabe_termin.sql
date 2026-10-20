-- Geplante Veröffentlichung einer Freigabe (für den Freigabe-Kalender)
BEGIN;
ALTER TABLE kundenfreigaben ADD COLUMN IF NOT EXISTS veroeffentlichung_am date;
CREATE INDEX IF NOT EXISTS kundenfreigaben_termin_idx ON kundenfreigaben (veroeffentlichung_am) WHERE veroeffentlichung_am IS NOT NULL;
COMMIT;
