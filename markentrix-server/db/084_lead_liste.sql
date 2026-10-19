-- Leads aus Excel/CSV-Import: Name der Importliste zum Filtern
ALTER TABLE leads ADD COLUMN IF NOT EXISTS liste text;
CREATE INDEX IF NOT EXISTS leads_liste_idx ON leads (liste) WHERE liste IS NOT NULL;
