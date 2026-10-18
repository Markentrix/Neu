-- 015 Kundenbereich: Projekte, Websites, Anfragen, Termine, Kontakte, Angebote, Verträge,
-- Wochenangebote-Uploads, Chatverlauf, Berichte.
BEGIN;

CREATE TABLE projekte (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  titel text NOT NULL,
  art text NOT NULL DEFAULT 'website' CHECK (art IN ('website','landingpage','kampagne','automation','ci','sonstiges')),
  status text NOT NULL DEFAULT 'geplant' CHECK (status IN ('geplant','in_arbeit','zur_abnahme','live','pausiert','fertig')),
  buchung_id uuid REFERENCES buchungen(id) ON DELETE SET NULL,
  url text, beschreibung text,
  erstellt_am timestamptz NOT NULL DEFAULT now(), geaendert_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX projekte_kunde_idx ON projekte (kunden_id);
CREATE TRIGGER projekte_geaendert BEFORE UPDATE ON projekte FOR EACH ROW EXECUTE FUNCTION set_geaendert();
SELECT rls_kunde('projekte', false);

-- Kunden-Websites auf dem Server (Verweis auf Ordner unter /srv/sites)
CREATE TABLE websites (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  domain text NOT NULL UNIQUE,
  art text NOT NULL DEFAULT 'live' CHECK (art IN ('live','demo')),
  status text NOT NULL DEFAULT 'geplant' CHECK (status IN ('geplant','demo','live','pausiert','offline')),
  verzeichnis text,
  domain_anbieter text,                      -- z. B. INWX oder Kunde selbst
  ssl_bis date,
  letzte_veroeffentlichung timestamptz,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX websites_kunde_idx ON websites (kunden_id);
SELECT rls_kunde('websites', false);

CREATE TABLE anfragen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  name text, kontakt text, nachricht text,
  quelle text NOT NULL DEFAULT 'website' CHECK (quelle IN ('website','email','telefon','chat','whatsapp','sonstiges')),
  status text NOT NULL DEFAULT 'neu' CHECK (status IN ('neu','in_bearbeitung','beantwortet','erledigt','spam')),
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX anfragen_kunde_idx ON anfragen (kunden_id, erstellt_am DESC);
SELECT rls_kunde('anfragen', true);

CREATE TABLE termine (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  anfrage_id uuid REFERENCES anfragen(id) ON DELETE SET NULL,
  titel text NOT NULL, beginn timestamptz NOT NULL, ende timestamptz,
  kontakt_name text, kontakt_info text,
  status text NOT NULL DEFAULT 'geplant' CHECK (status IN ('geplant','bestaetigt','abgesagt','erledigt','nicht_erschienen')),
  erinnerung_gesendet boolean NOT NULL DEFAULT false,
  kalender_ref text, notiz text,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX termine_kunde_idx ON termine (kunden_id, beginn);
SELECT rls_kunde('termine', true);

CREATE TABLE kontakte (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  name text NOT NULL, firma text, email text, telefon text, notiz text,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX kontakte_kunde_idx ON kontakte (kunden_id);
SELECT rls_kunde('kontakte', true);

CREATE TABLE angebote (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  nummer text, titel text NOT NULL, betrag_cent bigint,
  status text NOT NULL DEFAULT 'entwurf' CHECK (status IN ('entwurf','zur_freigabe','versendet','angenommen','abgelehnt','abgelaufen')),
  dateipfad text, gueltig_bis date,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX angebote_kunde_idx ON angebote (kunden_id);
SELECT rls_kunde('angebote', false);

CREATE TABLE vertraege (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  buchung_id uuid REFERENCES buchungen(id) ON DELETE SET NULL,
  titel text NOT NULL, beginn date, ende date,
  status text NOT NULL DEFAULT 'entwurf' CHECK (status IN ('entwurf','zur_unterschrift','aktiv','gekuendigt','beendet')),
  unterschrieben_am timestamptz, dateipfad text,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX vertraege_kunde_idx ON vertraege (kunden_id);
SELECT rls_kunde('vertraege', false);

CREATE TABLE wochenangebote_uploads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  website_id uuid REFERENCES websites(id) ON DELETE SET NULL,
  dateiname text NOT NULL,
  mime text NOT NULL CHECK (mime IN ('application/pdf','image/jpeg','image/png')),
  groesse bigint NOT NULL CHECK (groesse > 0 AND groesse <= 10485760),
  dateipfad text NOT NULL,
  status text NOT NULL DEFAULT 'hochgeladen' CHECK (status IN ('hochgeladen','wird_verarbeitet','veroeffentlicht','ersetzt','fehler')),
  gueltig_von date, gueltig_bis date, fehlertext text,
  hochgeladen_von uuid REFERENCES benutzer(id) ON DELETE SET NULL,
  erstellt_am timestamptz NOT NULL DEFAULT now(), veroeffentlicht_am timestamptz
);
CREATE INDEX wochenangebote_kunde_idx ON wochenangebote_uploads (kunden_id, erstellt_am DESC);
SELECT rls_kunde('wochenangebote_uploads', true);

CREATE TABLE chat_verlauf (
  id bigserial PRIMARY KEY,
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  benutzer_id uuid REFERENCES benutzer(id) ON DELETE SET NULL,
  absender text NOT NULL CHECK (absender IN ('kunde','agent')),
  text text NOT NULL, erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX chat_kunde_idx ON chat_verlauf (kunden_id, erstellt_am);
SELECT rls_kunde('chat_verlauf', true);

CREATE TABLE berichte (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  titel text NOT NULL,
  art text NOT NULL DEFAULT 'werbung' CHECK (art IN ('werbung','website','social','lokale_sichtbarkeit','sonstiges')),
  zeitraum_von date, zeitraum_bis date,
  daten jsonb NOT NULL DEFAULT '{}'::jsonb, dateipfad text,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX berichte_kunde_idx ON berichte (kunden_id);
SELECT rls_kunde('berichte', false);
COMMIT;
