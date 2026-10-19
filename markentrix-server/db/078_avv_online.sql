-- AVV per Klick im Portal bestätigen: Freigabe durch das Team, Nachweis der Bestätigung
ALTER TABLE avv ADD COLUMN IF NOT EXISTS portal_freigabe_am timestamptz;
ALTER TABLE avv ADD COLUMN IF NOT EXISTS online_bestaetigt_am timestamptz;
ALTER TABLE avv ADD COLUMN IF NOT EXISTS online_bestaetigt_name text;
ALTER TABLE avv ADD COLUMN IF NOT EXISTS online_bestaetigt_email text;
ALTER TABLE avv ADD COLUMN IF NOT EXISTS online_bestaetigt_ip text;
ALTER TABLE avv ADD COLUMN IF NOT EXISTS online_bestaetigt_hash text;   -- SHA-256 des bestätigten Textes

-- Erinnerung an Kunden im Onboarding (offene Schritte), höchstens einmal pro Woche
ALTER TABLE kunden ADD COLUMN IF NOT EXISTS onboarding_erinnert_am timestamptz;
