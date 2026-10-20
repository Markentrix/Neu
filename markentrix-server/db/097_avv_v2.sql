-- AVV Version 2: Anlage 1 (gebuchte Module) und Platzhalter je Vertrag speichern
BEGIN;
ALTER TABLE avv ADD COLUMN IF NOT EXISTS anlage jsonb NOT NULL DEFAULT '{}'::jsonb;
COMMIT;
