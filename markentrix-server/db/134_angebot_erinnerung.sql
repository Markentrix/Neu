-- Erinnerungen an unbeantwortete Angebote: wie oft und wann zuletzt (Begrenzung gegen zu häufiges Nachfragen)
ALTER TABLE belege ADD COLUMN IF NOT EXISTS erinnerungen int NOT NULL DEFAULT 0;
ALTER TABLE belege ADD COLUMN IF NOT EXISTS erinnert_am timestamptz;
