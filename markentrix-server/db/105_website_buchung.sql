-- Website-API für fertig gebaute Kunden-Websites (z. B. ElbDetail): feste Abgabezeiten, Tageslimit, Sperrtage, Freigabe durch den Inhaber, anonyme Statistik.
BEGIN;
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS kal_zeiten text;                      -- z. B. '08:00,10:00,13:00'; leer = Raster aus Beginn/Ende/Dauer
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS kal_kapazitaet int NOT NULL DEFAULT 0; -- Buchungen pro Tag, 0 = unbegrenzt
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS kal_freigabe boolean NOT NULL DEFAULT false; -- true: Inhaber bestätigt jede Buchung selbst
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS kal_halte_std int NOT NULL DEFAULT 72;      -- so lange bleibt eine unbestätigte Reservierung vorgemerkt
ALTER TABLE website_dienste ADD COLUMN IF NOT EXISTS stat_aktiv boolean NOT NULL DEFAULT true;

ALTER TABLE website_termine DROP CONSTRAINT IF EXISTS website_termine_status_check;
ALTER TABLE website_termine ADD CONSTRAINT website_termine_status_check CHECK (status IN ('gebucht','reserviert','abgesagt'));
ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS ref text;
ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS daten jsonb;
ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS anzahlung text;
DROP INDEX IF EXISTS website_termine_slot;
CREATE UNIQUE INDEX website_termine_slot ON website_termine (kunden_id, start) WHERE status IN ('gebucht','reserviert');

CREATE TABLE IF NOT EXISTS website_sperrtage (
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  tag date NOT NULL, grund text,
  PRIMARY KEY (kunden_id, tag)
);
SELECT rls_intern('website_sperrtage');

-- Anonyme Besucherstatistik: kein Cookie, keine IP-Adresse; die Besucherkennung ist ein täglich wechselnder Hash
CREATE TABLE IF NOT EXISTS website_stat (
  id bigserial PRIMARY KEY,
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  tag date NOT NULL DEFAULT current_date,
  art text NOT NULL CHECK (art IN ('pv','ev')),
  name text, pfad text, quelle text, geraet text, besucher text
);
CREATE INDEX IF NOT EXISTS website_stat_idx ON website_stat (kunden_id, tag);
SELECT rls_intern('website_stat');
COMMIT;
