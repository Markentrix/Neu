-- Admin-Werkzeuge: Textvorlagen (Mails, Aufgabenpakete), gespeicherte Filter, Betriebsstatus (Herzschlag der Hintergrundjobs, Mailversand)
CREATE TABLE IF NOT EXISTS textvorlagen (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  art          text NOT NULL CHECK (art IN ('mail','aufgaben')),
  name         text NOT NULL,
  betreff      text,
  text         text,
  aufgaben     jsonb NOT NULL DEFAULT '[]'::jsonb,
  erstellt_am  timestamptz NOT NULL DEFAULT now(),
  geaendert_am timestamptz NOT NULL DEFAULT now(),
  UNIQUE (art, name)
);
SELECT rls_intern('textvorlagen');

CREATE TABLE IF NOT EXISTS gespeicherte_filter (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  benutzer_id uuid NOT NULL REFERENCES benutzer(id) ON DELETE CASCADE,
  bereich     text NOT NULL CHECK (bereich IN ('leads','kunden','belege')),
  name        text NOT NULL,
  abfrage     text NOT NULL DEFAULT '',
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  UNIQUE (benutzer_id, bereich, name)
);
SELECT rls_intern('gespeicherte_filter');

CREATE TABLE IF NOT EXISTS betrieb_status (
  schluessel text PRIMARY KEY,
  wert       jsonb NOT NULL DEFAULT '{}'::jsonb,
  am         timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('betrieb_status');

INSERT INTO textvorlagen (art, name, betreff, text) VALUES
('mail', 'Willkommen / Onboarding', 'Willkommen bei Markentrix, {firma}',
 E'Guten Tag {name},\n\nschön, dass Sie dabei sind. Als Nächstes brauchen wir von Ihnen das Briefing, Ihr Logo und ein paar Fotos. Alles finden Sie in Ihrem Portal unter "Dein Start bei Markentrix".\n\nBei Fragen antworten Sie einfach auf diese Nachricht.\n\nViele Grüße\nIhr Markentrix-Team'),
('mail', 'Rückfrage zum Briefing', 'Kurze Rückfrage zu Ihrem Briefing ({firma})',
 E'Guten Tag {name},\n\nzu Ihrem Briefing haben wir noch eine kurze Rückfrage:\n\n[Frage]\n\nSobald wir Ihre Antwort haben, machen wir direkt weiter.\n\nViele Grüße\nIhr Markentrix-Team'),
('mail', 'Terminbestätigung', 'Ihr Termin mit Markentrix',
 E'Guten Tag {name},\n\nhiermit bestätigen wir unseren Termin am [Datum] um [Uhrzeit]. Wenn etwas dazwischenkommt, geben Sie uns bitte kurz Bescheid.\n\nViele Grüße\nIhr Markentrix-Team'),
('mail', 'Erinnerung: Freigabe wartet', 'Ihre Freigabe wartet noch ({firma})',
 E'Guten Tag {name},\n\nin Ihrem Portal wartet noch eine Freigabe auf Sie. Sobald Sie diese bestätigen, geht es bei uns weiter.\n\nViele Grüße\nIhr Markentrix-Team')
ON CONFLICT (art, name) DO NOTHING;

INSERT INTO textvorlagen (art, name, aufgaben) VALUES
('aufgaben', 'Neuer Kunde: 8 Schritte', '[
  {"titel":"Willkommensmail senden und Ersttermin vereinbaren","tage":1},
  {"titel":"AVV prüfen und unterschreiben lassen","tage":3},
  {"titel":"Briefing mit dem Kunden durchgehen","tage":5},
  {"titel":"Logo, Farben und Fotos einsammeln","tage":7},
  {"titel":"Zugänge zu externen Diensten einholen","tage":9},
  {"titel":"Website und Texte entwerfen","tage":14},
  {"titel":"KI-Assistent einrichten und testen","tage":18},
  {"titel":"Übergabe-Termin und Einweisung","tage":21}]'::jsonb)
ON CONFLICT (art, name) DO NOTHING;
