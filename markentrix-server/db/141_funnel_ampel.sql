-- Website-Ampel auf der Danke-Seite einer Funnel-Seite (je Seite abschaltbar)
ALTER TABLE lead_kampagnen ADD COLUMN IF NOT EXISTS ampel_zeigen boolean NOT NULL DEFAULT true;
