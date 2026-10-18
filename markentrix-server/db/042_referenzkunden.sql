-- Referenzkunden: bekommen Leistungen ohne Bezahlung, werden aber normal verwaltet
ALTER TABLE kunden ADD COLUMN IF NOT EXISTS referenzkunde boolean NOT NULL DEFAULT false;
ALTER TABLE kunden ADD COLUMN IF NOT EXISTS referenz_leistung text;
ALTER TABLE kunden ADD COLUMN IF NOT EXISTS referenz_nennen_erlaubt boolean NOT NULL DEFAULT false;
CREATE INDEX IF NOT EXISTS kunden_referenz_idx ON kunden (referenzkunde) WHERE referenzkunde;
