-- Anmeldung mit Passkey (Fingerabdruck, Face-ID, Geräte-PIN) nach WebAuthn.
CREATE TABLE IF NOT EXISTS passkeys (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  benutzer_id uuid NOT NULL REFERENCES benutzer(id) ON DELETE CASCADE,
  credential_id bytea NOT NULL UNIQUE,
  public_key bytea NOT NULL,          -- DER (SubjectPublicKeyInfo)
  alg integer NOT NULL,               -- -7 = ES256, -257 = RS256
  sign_count bigint NOT NULL DEFAULT 0,
  name text NOT NULL DEFAULT 'Dieses Gerät',
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  zuletzt_am timestamptz
);
CREATE INDEX IF NOT EXISTS passkeys_benutzer_idx ON passkeys (benutzer_id);
SELECT rls_intern('passkeys');
-- Einmal-Aufforderungen (Challenges), 5 Minuten gültig
CREATE UNLOGGED TABLE IF NOT EXISTS passkey_challenges (
  hash text PRIMARY KEY,
  benutzer_id uuid,
  art text NOT NULL CHECK (art IN ('registrieren','login')),
  ablauf timestamptz NOT NULL
);
ALTER TABLE sitzungen ADD COLUMN IF NOT EXISTS passkey boolean NOT NULL DEFAULT false;
