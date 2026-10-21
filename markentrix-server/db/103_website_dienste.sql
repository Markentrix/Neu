-- Website-Dienste: Kontaktformular, Terminbuchung, PayPal und Bewertungen für die Kunden-Websites.
-- Geheimnisse (SMTP-Zugang, Kalender-Adresse) liegen nur verschlüsselt in *_enc (Schlüssel in der .env), die Website selbst bekommt nie ein Geheimnis.
BEGIN;
CREATE TABLE IF NOT EXISTS website_dienste (
  kunden_id uuid PRIMARY KEY REFERENCES kunden(id) ON DELETE CASCADE,
  site_id text NOT NULL UNIQUE,
  mail_aktiv boolean NOT NULL DEFAULT false,
  mail_empfaenger text, mail_betreff text, mail_name text,
  smtp_enc text, smtp_absender text, smtp_geprueft_am timestamptz,
  kal_aktiv boolean NOT NULL DEFAULT false,
  kal_ical_enc text, kal_ical_geprueft_am timestamptz,
  kal_dauer int NOT NULL DEFAULT 30, kal_tage int NOT NULL DEFAULT 14,
  kal_von text NOT NULL DEFAULT '09:00', kal_bis text NOT NULL DEFAULT '17:00',
  kal_wochentage int[] NOT NULL DEFAULT '{1,2,3,4,5}', kal_vorlauf_std int NOT NULL DEFAULT 12,
  kal_ort text, kal_empfaenger text,
  pp_aktiv boolean NOT NULL DEFAULT false,
  pp_client_id text, pp_waehrung text NOT NULL DEFAULT 'EUR', pp_me_link text, pp_modus text NOT NULL DEFAULT 'live',
  bew_aktiv boolean NOT NULL DEFAULT false,
  bew_place_id text, bew_cache jsonb, bew_stand timestamptz,
  bew_sterne numeric(2,1), bew_anzahl int, bew_link text,
  geaendert_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('website_dienste');

CREATE TABLE IF NOT EXISTS website_termine (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  termin_id uuid REFERENCES termine(id) ON DELETE SET NULL,
  start timestamptz NOT NULL, ende timestamptz NOT NULL,
  name text NOT NULL, email text NOT NULL, telefon text, nachricht text,
  token text NOT NULL UNIQUE,
  status text NOT NULL DEFAULT 'gebucht' CHECK (status IN ('gebucht','abgesagt')),
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS website_termine_slot ON website_termine (kunden_id, start) WHERE status = 'gebucht';
SELECT rls_intern('website_termine');

CREATE TABLE IF NOT EXISTS website_ereignisse (
  id bigserial PRIMARY KEY,
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  art text NOT NULL, ok boolean NOT NULL, hinweis text,
  zeit timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS website_ereignisse_idx ON website_ereignisse (kunden_id, zeit DESC);
SELECT rls_intern('website_ereignisse');
COMMIT;
