-- Leistungen mit Anzahlung und eigener Freigabe, Zahlungsstand je Termin, Absageregel, Preisänderungen mit Freigabe des Teams.
BEGIN;
ALTER TABLE website_leistungen ADD COLUMN IF NOT EXISTS freigabe boolean NOT NULL DEFAULT false;
ALTER TABLE website_leistungen ADD COLUMN IF NOT EXISTS anzahlung_art text NOT NULL DEFAULT 'keine';
ALTER TABLE website_leistungen ADD COLUMN IF NOT EXISTS anzahlung_wert numeric(10,2);
ALTER TABLE website_leistungen DROP CONSTRAINT IF EXISTS website_leistungen_anzahlung_art_check;
ALTER TABLE website_leistungen ADD CONSTRAINT website_leistungen_anzahlung_art_check CHECK (anzahlung_art IN ('keine','betrag','prozent'));

ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS preis_betrag numeric(10,2);
ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS anzahlung_betrag numeric(10,2);
ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS anzahlung_erhalten_am timestamptz;
ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS bezahlt_am timestamptz;

ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS anz_frist_std int NOT NULL DEFAULT 0 CHECK (anz_frist_std BETWEEN 0 AND 720);
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS storno_std int NOT NULL DEFAULT 24 CHECK (storno_std BETWEEN 0 AND 168);
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS leistungen_freigabe boolean NOT NULL DEFAULT false;

CREATE TABLE IF NOT EXISTS website_leistung_aenderungen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  aktion text NOT NULL CHECK (aktion IN ('neu','aendern','loeschen')),
  leistung_id uuid, name text NOT NULL, daten jsonb NOT NULL DEFAULT '{}'::jsonb,
  status text NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','uebernommen','abgelehnt','zurueckgezogen')),
  notiz text, von uuid, erstellt_am timestamptz NOT NULL DEFAULT now(), bearbeitet_am timestamptz
);
CREATE INDEX IF NOT EXISTS website_leistung_aenderungen_idx ON website_leistung_aenderungen (kunden_id, status, erstellt_am DESC);
SELECT rls_intern('website_leistung_aenderungen');
COMMIT;
