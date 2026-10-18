-- Onboarding-Checkliste pro Kunde (nur intern sichtbar)
CREATE TABLE IF NOT EXISTS onboarding_punkte (
  id          bigserial PRIMARY KEY,
  kunden_id   uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  code        text NOT NULL,
  titel       text NOT NULL,
  hilfe       text,
  sortierung  int NOT NULL DEFAULT 100,
  erledigt    boolean NOT NULL DEFAULT false,
  erledigt_am timestamptz,
  notiz       text,
  UNIQUE (kunden_id, code)
);
CREATE INDEX IF NOT EXISTS onboarding_kunde_idx ON onboarding_punkte (kunden_id);
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'onboarding_punkte') THEN
    PERFORM rls_intern('onboarding_punkte');
  END IF;
END $$;
