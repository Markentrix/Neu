-- Provisionen: Verlängerungsbonus, Rückbuchungen, Nachlauf nach Partner-Ende
ALTER TABLE provisionen ADD COLUMN IF NOT EXISTS art text NOT NULL DEFAULT 'laufend';
ALTER TABLE provisionen ADD COLUMN IF NOT EXISTS ursprung_id uuid REFERENCES provisionen(id);
ALTER TABLE provisionen ADD COLUMN IF NOT EXISTS notiz text;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'provisionen_art_check') THEN
    ALTER TABLE provisionen ADD CONSTRAINT provisionen_art_check CHECK (art IN ('laufend','verlaengerung','rueckbuchung'));
  END IF;
END $$;
ALTER TABLE provisionen DROP CONSTRAINT IF EXISTS provisionen_vertriebspartner_id_buchung_id_monat_key;
CREATE UNIQUE INDEX IF NOT EXISTS provisionen_eindeutig ON provisionen (vertriebspartner_id, buchung_id, monat, art);
ALTER TABLE vertriebspartner ADD COLUMN IF NOT EXISTS beendet_am date;
