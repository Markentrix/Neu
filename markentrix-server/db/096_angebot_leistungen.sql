-- Angebote zeigen, was der Kunde genau bekommt: Leistungsumfang je Produkt (Vorlage) und je Angebot (anpassbar).
BEGIN;
ALTER TABLE belege ADD COLUMN IF NOT EXISTS leistungen jsonb NOT NULL DEFAULT '[]'::jsonb;
ALTER TABLE produkte ADD COLUMN IF NOT EXISTS leistungen jsonb NOT NULL DEFAULT '[]'::jsonb;

UPDATE produkte p SET leistungen = v.l::jsonb FROM (VALUES
 ('KI_ONE', '["KI-Assistent für WhatsApp oder E-Mail, rund um die Uhr erreichbar","1.500 Nachrichten im Monat inklusive","Einrichtung, Anbindung und Test durch uns","Kundenportal mit Anfragen, Terminen und Auswertung","12 Monate Laufzeit"]'),
 ('KI_BUSINESS', '["KI-Telefonagent und WhatsApp-Assistent, rund um die Uhr erreichbar","600 Minuten und 3.000 Nachrichten im Monat inklusive","Einrichtung, Anbindung und Test durch uns","Kundenportal mit Anfragen, Terminen und Auswertung","12 Monate Laufzeit"]'),
 ('KI_KOMPLETT', '["KI-Assistent für Telefon, WhatsApp und E-Mail, rund um die Uhr erreichbar","1.000 Minuten und 5.000 Nachrichten im Monat inklusive","Einrichtung, Anbindung und Test durch uns","Kundenportal mit Anfragen, Terminen und Auswertung","12 Monate Laufzeit"]'),
 ('WEB_LANDING_START', '["Eine Seite auf Vorlagenbasis im Design Ihrer Marke","Texte und Bilder liefern Sie, wir bauen und veröffentlichen","Hosting und Sicherung inklusive","Pflege während der Laufzeit, 12 Monate"]'),
 ('WEB_LANDING', '["Conversion-Onepager mit Texten und Bildern von uns","Terminbuchung direkt auf der Seite","SEO- und GEO-Grundlagen inklusive","Hosting und Sicherung inklusive","Pflege während der Laufzeit, 12 Monate"]'),
 ('WEB_BUSINESS', '["Bis zu sieben Inhaltsseiten, Struktur, Texte und Bilder entstehen bei uns","SEO- und GEO-Grundlagen inklusive, Livegang in der Regel in 5 bis 15 Werktagen","Pflege, 12 Monate Laufzeit, Hosting und Sicherung inklusive"]'),
 ('WEB_FUNNEL', '["Bis zu zwölf Seiten mit Anfrage- oder Verkaufsstrecke","Struktur, Texte und Bilder entstehen bei uns","SEO- und GEO-Grundlagen inklusive","Pflege, 12 Monate Laufzeit, Hosting und Sicherung inklusive"]'),
 ('CI_BASIC', '["Logo, Farbwelt und Schriftwelt für Ihren Auftritt","Alle Dateien für Druck und Bildschirm"]'),
 ('CI_BUSINESS', '["Logo, Farbwelt und Schriftwelt","Visitenkarte, Briefbogen und Vorlagen","Alle Dateien für Druck und Bildschirm"]'),
 ('CI_PREMIUM', '["Logo, Farbwelt und Schriftwelt","Visitenkarte, Briefbogen und Vorlagen","Markenhandbuch und Social-Kit","Alle Dateien für Druck und Bildschirm"]'),
 ('SOCIAL_MEDIA', '["Vier Beiträge im Monat auf zwei Kanälen","Redaktionsplan und Abstimmung mit Ihnen","Monatliches Reporting","12 Monate Laufzeit"]'),
 ('LOCAL_VISIBILITY', '["Google-Unternehmensprofil einrichten und pflegen","Lokale Suchmaschinenoptimierung","Bewertungen im Blick und Antwortvorschläge","12 Monate Laufzeit"]'),
 ('BEWERTUNGSANFRAGEN', '["Automatische Bewertungsanfrage nach Auftragsabschluss","Mehr Google-Bewertungen ohne Aufwand","12 Monate Laufzeit"]'),
 ('NEWSLETTER', '["Aufbau des Newsletter-Systems mit Vorlagen","Versand und Auswertung","12 Monate Laufzeit"]'),
 ('GBP_POSTINGS', '["Regelmäßige Beiträge in Ihrem Google-Profil","Abstimmung der Themen mit Ihnen","12 Monate Laufzeit"]'),
 ('PB_ESSENTIAL', '["Vier Beiträge im Monat","Profilaufbau und Redaktionsplan"]'),
 ('PB_GROWTH', '["Acht Inhalte im Monat","Themenplanung und Grafiken"]'),
 ('PB_AUTHORITY', '["12 bis 16 Inhalte im Monat","Strategie und Positionierung"]')
) AS v(code, l) WHERE p.code = v.code AND p.leistungen = '[]'::jsonb;
COMMIT;
