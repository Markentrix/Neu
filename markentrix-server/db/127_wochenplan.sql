-- Arbeitszeiten je Wochentag mit mehreren Zeitfenstern (Pausen): {"1": [["09:00","12:00"],["13:00","18:00"]], "6": [["09:00","14:00"]]}.
-- NULL = bisherige Einstellung (Wochentage, Beginn, Ende).
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS kal_wochenplan jsonb;
ALTER TABLE website_mitarbeiter ADD COLUMN IF NOT EXISTS wochenplan jsonb;
