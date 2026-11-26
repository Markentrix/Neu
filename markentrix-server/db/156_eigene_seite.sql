-- Eigene Website (markentrix.de) im Portal verwalten: unsichtbarer interner Eintrag ohne Login (Status "intern").
-- Alle Auswertungen, Jobs und Listen filtern auf feste Status (aktiv, onboarding, ...), "intern" fällt dort heraus.
BEGIN;
DO $$
DECLARE c text;
BEGIN
  FOR c IN SELECT conname FROM pg_constraint
           WHERE conrelid = 'kunden'::regclass AND contype = 'c'
             AND pg_get_constraintdef(oid) LIKE '%status%' AND pg_get_constraintdef(oid) LIKE '%gekuendigt%' AND pg_get_constraintdef(oid) LIKE '%beendet%'
  LOOP
    EXECUTE format('ALTER TABLE kunden DROP CONSTRAINT %I', c);
  END LOOP;
END $$;
ALTER TABLE kunden ADD CONSTRAINT kunden_status_check CHECK (status IN ('onboarding','aktiv','pausiert','gekuendigt','beendet','intern'));
CREATE UNIQUE INDEX IF NOT EXISTS kunden_intern_eindeutig ON kunden ((true)) WHERE status = 'intern';
COMMIT;
