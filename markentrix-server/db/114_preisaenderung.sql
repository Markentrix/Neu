-- Preiserhöhung per Knopfdruck: Ankündigung mit Frist, Widerspruch, automatische Anwendung zum Stichtag
BEGIN;
CREATE TABLE IF NOT EXISTS preisaenderungen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  titel text NOT NULL,
  prozent numeric(5,2) NOT NULL CHECK (prozent > 0 AND prozent <= 25),
  wirksam_ab date NOT NULL,
  text text NOT NULL DEFAULT '',
  status text NOT NULL DEFAULT 'entwurf' CHECK (status IN ('entwurf','angekuendigt','angewendet','abgebrochen')),
  angekuendigt_am timestamptz,
  angewendet_am timestamptz,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('preisaenderungen');
CREATE TABLE IF NOT EXISTS preisaenderung_kunden (
  preisaenderung_id uuid NOT NULL REFERENCES preisaenderungen(id) ON DELETE CASCADE,
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  token text NOT NULL UNIQUE,
  alt_cent bigint NOT NULL,
  neu_cent bigint NOT NULL,
  benachrichtigt_am timestamptz,
  gelesen_am timestamptz,
  widerspruch_am timestamptz,
  widerspruch_text text,
  angewendet_am timestamptz,
  PRIMARY KEY (preisaenderung_id, kunden_id)
);
SELECT rls_intern('preisaenderung_kunden');
COMMIT;
