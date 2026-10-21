-- Betrieb der Kunden-Websites: Terminerinnerungen an die Besucher, Nichterschienen-Zähler, Überwachung, Vorschau-Freigabe.
BEGIN;
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS erinnerung_aktiv boolean NOT NULL DEFAULT true;
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS erinnerung_std1 int NOT NULL DEFAULT 24 CHECK (erinnerung_std1 BETWEEN 0 AND 168);   -- 0 = aus
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS erinnerung_std2 int NOT NULL DEFAULT 2 CHECK (erinnerung_std2 BETWEEN 0 AND 48);

ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS erinnerung int NOT NULL DEFAULT 0;         -- 0 nichts, 1 erste, 2 zweite Erinnerung erledigt
ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS ergebnis text CHECK (ergebnis IN ('erschienen','nicht_erschienen'));
CREATE INDEX IF NOT EXISTS website_termine_email_idx ON website_termine (kunden_id, lower(email)) WHERE ergebnis = 'nicht_erschienen';

-- Überwachung: letzter Stand je Website und Tageszähler für die Erreichbarkeit
CREATE TABLE IF NOT EXISTS website_wacht (
  domain text PRIMARY KEY,
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  geprueft_am timestamptz NOT NULL DEFAULT now(),
  ok boolean NOT NULL, seite_ok boolean NOT NULL DEFAULT false, api_ok boolean NOT NULL DEFAULT false,
  http int, ms int, cert_tage int, fehler text,
  seit timestamptz NOT NULL DEFAULT now(),           -- seit wann gilt der aktuelle Zustand
  fehlversuche int NOT NULL DEFAULT 0, gemeldet boolean NOT NULL DEFAULT false, cert_gemeldet_am timestamptz
);
SELECT rls_intern('website_wacht');
CREATE TABLE IF NOT EXISTS website_wacht_tag (
  domain text NOT NULL, tag date NOT NULL, geprueft int NOT NULL DEFAULT 0, ok int NOT NULL DEFAULT 0,
  PRIMARY KEY (domain, tag)
);
SELECT rls_intern('website_wacht_tag');

-- Vorschau-Freigabe: die Freigabe gehört zu einer Demo-Seite
ALTER TABLE kundenfreigaben ADD COLUMN IF NOT EXISTS demo_name text;
COMMIT;
