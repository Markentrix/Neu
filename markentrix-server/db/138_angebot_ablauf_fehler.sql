-- Abgelaufene Angebote einmal melden; Zustellfehler beim Angebotsversand festhalten.
ALTER TABLE belege ADD COLUMN IF NOT EXISTS ablauf_gemeldet_am timestamptz;
ALTER TABLE belege ADD COLUMN IF NOT EXISTS mail_fehler text;
ALTER TABLE belege ADD COLUMN IF NOT EXISTS mail_fehler_am timestamptz;
