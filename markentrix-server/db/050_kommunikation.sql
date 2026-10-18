-- 050 Kommunikation und Inhalte: Nachrichten, Anrufe, Social/GBP, Bewertungen, Newsletter.
BEGIN;

CREATE TABLE nachrichten (
  id bigserial PRIMARY KEY,
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  kanal text NOT NULL CHECK (kanal IN ('email','whatsapp','website_chat','telefon','sms')),
  richtung text NOT NULL CHECK (richtung IN ('ein','aus')),
  absender text, empfaenger text, betreff text, text text,
  ki_gekennzeichnet boolean NOT NULL DEFAULT true,       -- EU AI Act, Art. 50
  agent_lauf_id bigint REFERENCES agent_laeufe(id) ON DELETE SET NULL,
  anfrage_id uuid REFERENCES anfragen(id) ON DELETE SET NULL,
  extern_ref text, zeit timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX nachrichten_kunde_idx ON nachrichten (kunden_id, zeit DESC);
SELECT rls_kunde('nachrichten', false);

CREATE TABLE anrufe (
  id bigserial PRIMARY KEY,
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  richtung text NOT NULL CHECK (richtung IN ('ein','aus')),
  nummer text, beginn timestamptz NOT NULL DEFAULT now(), dauer_sek int,
  ergebnis text, zusammenfassung text, ki_hinweis_gegeben boolean NOT NULL DEFAULT false,
  aufnahme_erlaubt boolean NOT NULL DEFAULT false, extern_ref text
);
CREATE INDEX anrufe_kunde_idx ON anrufe (kunden_id, beginn DESC);
SELECT rls_kunde('anrufe', false);

CREATE TABLE content_plaene (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  zeitraum_von date NOT NULL, zeitraum_bis date NOT NULL, thema text,
  status text NOT NULL DEFAULT 'entwurf' CHECK (status IN ('entwurf','zur_freigabe','freigegeben','abgeschlossen')),
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_kunde('content_plaene', false);

CREATE TABLE content_beitraege (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  plan_id uuid REFERENCES content_plaene(id) ON DELETE SET NULL,
  kanal text NOT NULL CHECK (kanal IN ('instagram','facebook','linkedin','tiktok','google_business','newsletter','website')),
  text text, bild_ref text, geplant_fuer timestamptz,
  status text NOT NULL DEFAULT 'entwurf' CHECK (status IN ('entwurf','zur_freigabe','freigegeben','veroeffentlicht','abgelehnt','fehler')),
  freigabe_id uuid REFERENCES freigaben(id), veroeffentlicht_am timestamptz, extern_ref text,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX content_beitraege_kunde_idx ON content_beitraege (kunden_id, geplant_fuer);
SELECT rls_kunde('content_beitraege', false);

CREATE TABLE bewertungsanfragen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  empfaenger_kontakt text NOT NULL, ausloeser text,
  status text NOT NULL DEFAULT 'geplant' CHECK (status IN ('geplant','gesendet','bewertet','abgelehnt','fehler')),
  gesendet_am timestamptz, erstellt_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_kunde('bewertungsanfragen', false);

CREATE TABLE newsletter_kampagnen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  betreff text NOT NULL, inhalt text,
  status text NOT NULL DEFAULT 'entwurf' CHECK (status IN ('entwurf','zur_freigabe','geplant','gesendet')),
  empfaenger_anzahl int, geoeffnet int, geklickt int, gesendet_am timestamptz,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_kunde('newsletter_kampagnen', false);
COMMIT;
