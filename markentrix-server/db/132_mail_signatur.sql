-- Signatur für Mails, die über die Website-Dienste im Namen des Kunden verschickt werden (leer = „Mit freundlichen Grüßen, Firma“)
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS mail_signatur text;
-- Kleine Bausteine unter der Signatur: Google-Bewertung anbieten (nutzt den Bewertungs-Link der Website-Dienste), Social-Links, Vertraulichkeitshinweis
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS mail_bewertung boolean NOT NULL DEFAULT false;
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS mail_facebook text;
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS mail_instagram text;
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS mail_hinweis text;
