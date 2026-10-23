-- Preisstand laut Website (Preisliste vom 1. Oktober 2026), Pilot-Nachlass und weitere buchbare Leistungen (Preis auf Anfrage)
INSERT INTO konditionen (schluessel, wert_text, wert_zahl, beschreibung) VALUES
 ('preisstand', 'Stand 1. Oktober 2026', NULL, 'Alle Preise netto zuzüglich gesetzlicher Umsatzsteuer'),
 ('pilot_plaetze_ki', NULL, 2, 'Pilotplätze KI-Kundenkommunikation: Nachlass auf die Einrichtung für die ersten Kunden (0 = aus)'),
 ('pilot_nachlass_prozent', NULL, 50, 'Pilot-Nachlass auf die Einrichtung in Prozent')
ON CONFLICT (schluessel) DO UPDATE SET wert_text = EXCLUDED.wert_text, wert_zahl = COALESCE(EXCLUDED.wert_zahl, konditionen.wert_zahl), beschreibung = EXCLUDED.beschreibung;

INSERT INTO produkte (code, kategorie, name, beschreibung, abrechnung, laufzeit_monate, nur_auf_anfrage, einzeln_buchbar, sortierung) VALUES
 ('WEB_RELAUNCH', 'website', 'Website-Relaunch', 'Neuaufbau einer bestehenden Website. Preis nach Umfang, wir erstellen ein Angebot.', 'projekt', NULL, true, true, 25),
 ('WEB_PFLEGE', 'website', 'Website-Pflege', 'Hosting, Updates, Sicherung und kleine Änderungen für eine bestehende Website. Preis nach Aufwand.', 'monatlich', 12, true, true, 26),
 ('SEO_GEO', 'sichtbarkeit', 'SEO und GEO', 'Auffindbarkeit in Suchmaschinen und KI-Antworten über die Grundlagen hinaus. Grundlagen sind in jeder Website enthalten.', 'monatlich', 12, true, true, 45),
 ('GOOGLE_PROFIL', 'sichtbarkeit', 'Google-Unternehmensprofil', 'Einrichtung und Optimierung Ihres Google-Unternehmensprofils. Preis auf Anfrage.', 'projekt', NULL, true, true, 46)
ON CONFLICT (code) DO NOTHING;
