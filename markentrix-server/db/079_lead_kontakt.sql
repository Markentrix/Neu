-- Wiedervorlage für Leads (nächster Kontakt), gesetzt über das Kontaktergebnis
ALTER TABLE leads ADD COLUMN IF NOT EXISTS wiedervorlage_am date;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS letzter_kontakt_am timestamptz;
