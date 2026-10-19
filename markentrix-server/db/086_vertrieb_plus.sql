-- KI-Gesprächsleitfaden je Lead, Anmelde-Link per Mail
ALTER TABLE leads ADD COLUMN IF NOT EXISTS skript jsonb;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS skript_am timestamptz;

CREATE TABLE IF NOT EXISTS login_links (
  token_hash text PRIMARY KEY,
  benutzer_id uuid NOT NULL REFERENCES benutzer(id) ON DELETE CASCADE,
  ablauf timestamptz NOT NULL,
  benutzt_am timestamptz,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS login_links_benutzer_idx ON login_links (benutzer_id, erstellt_am DESC);
SELECT rls_intern('login_links');
