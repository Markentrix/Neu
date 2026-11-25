-- Zahlungsfrist je Rechnung (0 = sofort); leer = Standard aus den Firmeneinstellungen
ALTER TABLE belege ADD COLUMN IF NOT EXISTS zahlungsziel_tage integer CHECK (zahlungsziel_tage BETWEEN 0 AND 90);
