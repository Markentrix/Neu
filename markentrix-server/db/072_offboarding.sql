-- Vertragsende: Kennzeichnung, dass die Inhalte eines Kunden gelöscht wurden (Stammdaten und Belege bleiben wegen Aufbewahrungspflichten)
ALTER TABLE kunden ADD COLUMN IF NOT EXISTS geloescht_am timestamptz;
