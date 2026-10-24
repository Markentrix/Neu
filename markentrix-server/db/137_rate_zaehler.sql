-- Zähler für die Begrenzung von Anfragen (Anmeldung, öffentliche Formulare …). In der Datenbank statt im Arbeitsspeicher,
-- damit die Sperre einen Neustart überlebt und für alle Prozesse gilt. UNLOGGED: schnell, bei einem Absturz leer (unkritisch).
CREATE UNLOGGED TABLE IF NOT EXISTS rate_zaehler (
  schluessel text PRIMARY KEY,
  fenster_start timestamptz NOT NULL DEFAULT now(),
  anzahl int NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS rate_zaehler_alt ON rate_zaehler (fenster_start);
