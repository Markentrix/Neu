-- Zufriedenheitsumfrage (im Portal), Einwilligungsprotokoll der Kunden, Tages-Erinnerung für Vertriebler
BEGIN;
CREATE TABLE IF NOT EXISTS kunden_umfragen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  art text NOT NULL DEFAULT 'quartal' CHECK (art IN ('start','quartal')),
  angelegt_am timestamptz NOT NULL DEFAULT now(),
  beantwortet_am timestamptz,
  punkte smallint CHECK (punkte BETWEEN 0 AND 10),
  kommentar text,
  verfallen boolean NOT NULL DEFAULT false,
  mail_gesendet_am timestamptz
);
CREATE UNIQUE INDEX IF NOT EXISTS kunden_umfragen_offen ON kunden_umfragen (kunden_id) WHERE beantwortet_am IS NULL AND NOT verfallen;
CREATE INDEX IF NOT EXISTS kunden_umfragen_zeit ON kunden_umfragen (kunden_id, angelegt_am DESC);
SELECT rls_intern('kunden_umfragen');
CREATE TABLE IF NOT EXISTS kunden_einwilligungen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  art text NOT NULL CHECK (art IN ('umfrage_mail')),
  erteilt boolean NOT NULL,
  zeit timestamptz NOT NULL DEFAULT now(),
  ip text,
  benutzer text
);
CREATE INDEX IF NOT EXISTS kunden_einwilligungen_idx ON kunden_einwilligungen (kunden_id, art, zeit DESC);
SELECT rls_intern('kunden_einwilligungen');
ALTER TABLE vertriebspartner ADD COLUMN IF NOT EXISTS erinnerung_mail boolean NOT NULL DEFAULT true;
ALTER TABLE vertriebspartner ADD COLUMN IF NOT EXISTS erinnerung_am date;
COMMIT;
