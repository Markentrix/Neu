-- Rückgängig bei Sammelaktionen: Aufgaben einer Aktion tragen dieselbe Kennung
ALTER TABLE aufgaben ADD COLUMN IF NOT EXISTS sammel_id uuid;
CREATE INDEX IF NOT EXISTS aufgaben_sammel_idx ON aufgaben (sammel_id) WHERE sammel_id IS NOT NULL;
