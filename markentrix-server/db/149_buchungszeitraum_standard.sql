-- Online-Terminbuchung: neue Betriebe können standardmäßig 90 Tage im Voraus buchen (bisher 14). Bestehende Einstellungen bleiben unverändert.
ALTER TABLE website_dienste ALTER COLUMN kal_tage SET DEFAULT 90;
