-- Monatsbericht: Einordnung und nächste Schritte (automatisch erzeugt, vom Team überschreibbar)
ALTER TABLE berichte ADD COLUMN IF NOT EXISTS einordnung text;
ALTER TABLE berichte ADD COLUMN IF NOT EXISTS naechste_schritte text;       -- eine Zeile je Schritt
ALTER TABLE berichte ADD COLUMN IF NOT EXISTS einordnung_geaendert_am timestamptz;
