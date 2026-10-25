-- Lead-Funnel: Plätze pro Monat. Ist plaetze_monatlich gesetzt, stellt der Hintergrunddienst am Monatsanfang „frei“ wieder auf „insgesamt“;
-- die Seite nennt den laufenden Monat („im November“). plaetze_monat = Monat, für den der Zähler gerade gilt.
ALTER TABLE lead_kampagnen ADD COLUMN IF NOT EXISTS plaetze_monatlich boolean NOT NULL DEFAULT false;
ALTER TABLE lead_kampagnen ADD COLUMN IF NOT EXISTS plaetze_monat date;
