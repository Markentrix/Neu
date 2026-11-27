-- 159 AGB: Versionen (PDF) und Nachweis der Bestätigung durch Kunden bei der Anmeldung im Portal.
-- Genau eine Version ist aktiv. mitsenden = PDF hängt an Angebots- und Rechnungs-Mails, login_pflicht = Inhaber bestätigen beim Anmelden.
BEGIN;
CREATE TABLE IF NOT EXISTS agb_versionen (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  version        text NOT NULL,
  dateiname      text NOT NULL,
  datei          bytea NOT NULL,
  sha256         text NOT NULL,
  aktiv          boolean NOT NULL DEFAULT false,
  mitsenden      boolean NOT NULL DEFAULT true,
  login_pflicht  boolean NOT NULL DEFAULT true,
  hochgeladen_von text,
  erstellt_am    timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS agb_versionen_eine_aktiv ON agb_versionen ((true)) WHERE aktiv;
SELECT rls_intern('agb_versionen');

CREATE TABLE IF NOT EXISTS agb_zustimmungen (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id   uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  agb_id      uuid NOT NULL REFERENCES agb_versionen(id),
  benutzer_id uuid,
  benutzer    text,
  version     text NOT NULL,
  sha256      text NOT NULL,
  zeit        timestamptz NOT NULL DEFAULT now(),
  ip          text,
  user_agent  text
);
CREATE INDEX IF NOT EXISTS agb_zustimmungen_idx ON agb_zustimmungen (kunden_id, agb_id);
SELECT rls_intern('agb_zustimmungen');
COMMIT;
