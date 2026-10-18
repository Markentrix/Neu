-- Zwei-Faktor-Anmeldung (TOTP) und Rechtstexte
ALTER TABLE benutzer ADD COLUMN IF NOT EXISTS totp_secret text;            -- verschlüsselt (Fernet)
ALTER TABLE benutzer ADD COLUMN IF NOT EXISTS totp_aktiv boolean NOT NULL DEFAULT false;
ALTER TABLE benutzer ADD COLUMN IF NOT EXISTS totp_letzter_schritt bigint NOT NULL DEFAULT 0;
ALTER TABLE benutzer ADD COLUMN IF NOT EXISTS totp_recovery jsonb NOT NULL DEFAULT '[]'::jsonb;   -- SHA-256-Hashes der Notfallcodes
