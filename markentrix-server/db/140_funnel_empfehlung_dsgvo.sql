-- Lead-Funnel (Kampagnen mit eigener Anmeldeseite), Empfehlungsprogramm, Anfragen nach Art. 15 bis 21 DSGVO.
-- Alles ist ausgeschaltet, bis es im Admin freigegeben ist. Kampagnen gehen erst live, wenn der Rechtstext als geprüft eingetragen ist.

CREATE TABLE lead_kampagnen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug text NOT NULL UNIQUE CHECK (slug ~ '^[a-z0-9][a-z0-9-]{1,39}$'),
  name text NOT NULL,
  aktiv boolean NOT NULL DEFAULT false,
  rechtlich_geprueft_am date,
  titel text NOT NULL DEFAULT '',
  untertitel text NOT NULL DEFAULT '',
  nutzen text[] NOT NULL DEFAULT '{}',
  button text NOT NULL DEFAULT 'Kostenlos anfragen',
  einwilligung_text text NOT NULL DEFAULT '',
  danke_titel text NOT NULL DEFAULT 'Vielen Dank!',
  danke_text text NOT NULL DEFAULT 'Wir melden uns in Kürze bei Ihnen.',
  telefon_pflicht boolean NOT NULL DEFAULT true,
  website_abfragen boolean NOT NULL DEFAULT true,
  termin_anbieten boolean NOT NULL DEFAULT true,
  kosten_cent int NOT NULL DEFAULT 0 CHECK (kosten_cent >= 0),
  notiz text,
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  geaendert_am timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER lead_kampagnen_geaendert BEFORE UPDATE ON lead_kampagnen FOR EACH ROW EXECUTE FUNCTION set_geaendert();
SELECT rls_intern('lead_kampagnen');

CREATE TABLE lead_kampagnen_tage (
  kampagne_id uuid NOT NULL REFERENCES lead_kampagnen(id) ON DELETE CASCADE,
  tag date NOT NULL DEFAULT current_date,
  aufrufe int NOT NULL DEFAULT 0,
  PRIMARY KEY (kampagne_id, tag)
);
SELECT rls_intern('lead_kampagnen_tage');

ALTER TABLE leads ADD COLUMN IF NOT EXISTS kampagne_id uuid REFERENCES lead_kampagnen(id) ON DELETE SET NULL;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS utm jsonb;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS empfohlen_von uuid REFERENCES kunden(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS leads_kampagne_idx ON leads (kampagne_id) WHERE kampagne_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS leads_empfohlen_idx ON leads (empfohlen_von) WHERE empfohlen_von IS NOT NULL;

-- Die Kampagne für Empfehlungen von Kunden ist fest angelegt (ausgeschaltet).
INSERT INTO lead_kampagnen (slug, name, titel, untertitel, nutzen, button, einwilligung_text, termin_anbieten, notiz) VALUES
 ('empfehlung', 'Empfehlung durch Kunden', 'Sie wurden empfohlen', 'Lernen Sie Markentrix kennen: KI-Automatisierung für lokale Betriebe.',
  ARRAY['Weniger Büroarbeit durch Automatik','Anfragen und Termine laufen von selbst','Persönlicher Ansprechpartner'], 'Unverbindlich kennenlernen',
  'Ich bin einverstanden, dass Markentrix mich zu meiner Anfrage per Telefon und E-Mail kontaktiert. Hinweise im Datenschutz.', true,
  'Feste Kampagne für das Empfehlungsprogramm. Rechtstext vor dem Einschalten prüfen lassen.');

CREATE TABLE empfehlungs_praemien (
  lead_id uuid PRIMARY KEY REFERENCES leads(id) ON DELETE CASCADE,
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  status text NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','ausgezahlt','verworfen')),
  betrag_cent int CHECK (betrag_cent IS NULL OR betrag_cent >= 0),
  notiz text,
  geaendert_am timestamptz NOT NULL DEFAULT now()
);
CREATE TRIGGER empfehlungs_praemien_geaendert BEFORE UPDATE ON empfehlungs_praemien FOR EACH ROW EXECUTE FUNCTION set_geaendert();
SELECT rls_intern('empfehlungs_praemien');

ALTER TABLE kunden ADD COLUMN IF NOT EXISTS empfehlungscode text UNIQUE;

CREATE TABLE datenschutz_anfragen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  art text NOT NULL CHECK (art IN ('auskunft','loeschung','berichtigung','widerspruch','einschraenkung','uebertragung','sonstiges')),
  name text NOT NULL,
  email text,
  telefon text,
  nachricht text,
  quelle text NOT NULL DEFAULT 'manuell' CHECK (quelle IN ('manuell','formular','mail','brief','telefon')),
  status text NOT NULL DEFAULT 'neu' CHECK (status IN ('neu','in_arbeit','erledigt','abgelehnt')),
  identitaet_geprueft boolean NOT NULL DEFAULT false,
  eingang_am date NOT NULL DEFAULT current_date,
  frist_am date NOT NULL,
  erledigt_am date,
  notiz text,
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  geaendert_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX datenschutz_anfragen_offen_idx ON datenschutz_anfragen (frist_am) WHERE status IN ('neu','in_arbeit');
CREATE TRIGGER datenschutz_anfragen_geaendert BEFORE UPDATE ON datenschutz_anfragen FOR EACH ROW EXECUTE FUNCTION set_geaendert();
SELECT rls_intern('datenschutz_anfragen');
