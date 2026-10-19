-- Einstufung der Leads: kalt / warm / heiss (frei vom Status, vom Admin gesetzt)
ALTER TABLE leads ADD COLUMN IF NOT EXISTS temperatur text CHECK (temperatur IN ('kalt','warm','heiss'));
