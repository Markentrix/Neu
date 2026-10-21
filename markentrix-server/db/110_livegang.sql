-- DNS-Prüfung beim Livegang, Qualität der Websites, Bewertungsanfrage nach Termin, wiederkehrende Rechnungen
BEGIN;
CREATE TABLE IF NOT EXISTS domain_pruefung (
  domain text PRIMARY KEY,
  kunden_id uuid REFERENCES kunden(id) ON DELETE CASCADE,
  geprueft_am timestamptz NOT NULL DEFAULT now(),
  ok boolean NOT NULL DEFAULT false,
  ergebnis jsonb NOT NULL DEFAULT '{}'::jsonb,
  live_gemeldet boolean NOT NULL DEFAULT false
);
SELECT rls_intern('domain_pruefung');

CREATE TABLE IF NOT EXISTS website_qualitaet (
  domain text PRIMARY KEY,
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  geprueft_am timestamptz NOT NULL DEFAULT now(),
  seiten int NOT NULL DEFAULT 0, median_ms int, startseite_kb int,
  tote jsonb NOT NULL DEFAULT '[]'::jsonb, langsam jsonb NOT NULL DEFAULT '[]'::jsonb
);
SELECT rls_intern('website_qualitaet');

ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS bew_nach_termin boolean NOT NULL DEFAULT false;
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS bew_verzoegerung_std int NOT NULL DEFAULT 3 CHECK (bew_verzoegerung_std BETWEEN 1 AND 72);
ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS bewertung_faellig timestamptz;
ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS bewertung_gesendet timestamptz;
CREATE INDEX IF NOT EXISTS website_termine_bew_idx ON website_termine (bewertung_faellig) WHERE bewertung_gesendet IS NULL AND bewertung_faellig IS NOT NULL;
CREATE TABLE IF NOT EXISTS website_bewertung_sperre (
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  email text NOT NULL,
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (kunden_id, email)
);
SELECT rls_intern('website_bewertung_sperre');

CREATE TABLE IF NOT EXISTS abrechnungsplaene (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  titel text NOT NULL,
  intervall_monate int NOT NULL CHECK (intervall_monate IN (1,3,6,12)),
  aus_buchungen boolean NOT NULL DEFAULT false,     -- Positionen aus den monatlichen Preisen der Buchungen (mal Intervall)
  positionen jsonb NOT NULL DEFAULT '[]'::jsonb,    -- sonst feste Positionen (text, menge, einheit, preis_cent)
  naechste_am date NOT NULL,
  enddatum date,
  aktiv boolean NOT NULL DEFAULT true,
  auto_senden boolean NOT NULL DEFAULT false,
  zuletzt_beleg_id uuid, zuletzt_am date,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS abrechnungsplaene_faellig_idx ON abrechnungsplaene (naechste_am) WHERE aktiv;
SELECT rls_intern('abrechnungsplaene');
ALTER TABLE belege ADD COLUMN IF NOT EXISTS plan_id uuid;
CREATE UNIQUE INDEX IF NOT EXISTS belege_plan_lauf ON belege (plan_id, leistungszeitraum) WHERE plan_id IS NOT NULL AND storno_von IS NULL;
COMMIT;
