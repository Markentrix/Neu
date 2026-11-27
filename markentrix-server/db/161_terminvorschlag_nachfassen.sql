-- 161 Terminvorschläge: Nachfassen (von Hand per Knopf) festhalten
BEGIN;
ALTER TABLE terminvorschlaege ADD COLUMN IF NOT EXISTS nachgefasst_am timestamptz;
ALTER TABLE terminvorschlaege ADD COLUMN IF NOT EXISTS nachfass_anzahl int NOT NULL DEFAULT 0;
COMMIT;
