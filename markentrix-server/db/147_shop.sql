-- Online-Shop für Kunden-Websites: Artikel, Farben, Kategorien, Bilder, Bestellungen, Einstellungen. Alles gehört einem Kunden (Mandant).
INSERT INTO module (code,name,beschreibung,sortierung) VALUES
 ('shop','Online-Shop','Artikel, Bilder und Bestellungen der Website-Shops verwalten',9)
ON CONFLICT (code) DO NOTHING;

CREATE TABLE IF NOT EXISTS shop_einstellungen (
  kunden_id uuid PRIMARY KEY REFERENCES kunden(id) ON DELETE CASCADE,
  aktiv boolean NOT NULL DEFAULT false,                       -- erst wenn der Inhaber den Shop einschaltet, liefert die Schnittstelle Artikel aus
  ref_praefix text NOT NULL DEFAULT 'B' CHECK (ref_praefix ~ '^[A-Z0-9]{1,6}$'),
  versand_pauschale_cent integer NOT NULL DEFAULT 490 CHECK (versand_pauschale_cent BETWEEN 0 AND 100000),
  versandfrei_ab_cent integer CHECK (versandfrei_ab_cent IS NULL OR versandfrei_ab_cent BETWEEN 0 AND 10000000),
  abholung boolean NOT NULL DEFAULT true,
  produktionszeit text NOT NULL DEFAULT '' CHECK (length(produktionszeit) <= 200),
  lieferzeit text NOT NULL DEFAULT '' CHECK (length(lieferzeit) <= 200),
  gutschein_aktiv boolean NOT NULL DEFAULT false,
  gutschein_betraege integer[] NOT NULL DEFAULT '{10,20,30,50}',
  gutschein_min integer NOT NULL DEFAULT 10 CHECK (gutschein_min BETWEEN 1 AND 10000),
  gutschein_max integer NOT NULL DEFAULT 500 CHECK (gutschein_max BETWEEN 1 AND 10000),
  gutschein_monate integer NOT NULL DEFAULT 36 CHECK (gutschein_monate BETWEEN 1 AND 120),
  gutschein_zustellung text[] NOT NULL DEFAULT '{"E-Mail (PDF)","Post (Karte)"}',
  geaendert_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_kunde('shop_einstellungen', true);

CREATE TABLE IF NOT EXISTS shop_kategorien (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  schluessel text NOT NULL CHECK (schluessel ~ '^[a-z0-9][a-z0-9-]{0,48}$'),
  name text NOT NULL CHECK (length(name) BETWEEN 1 AND 80),
  sort integer NOT NULL DEFAULT 100,
  UNIQUE (kunden_id, schluessel)
);
SELECT rls_kunde('shop_kategorien', true);

CREATE TABLE IF NOT EXISTS shop_farben (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  schluessel text NOT NULL CHECK (schluessel ~ '^[a-z0-9][a-z0-9-]{0,48}$'),
  name text NOT NULL CHECK (length(name) BETWEEN 1 AND 80),
  hex text NOT NULL CHECK (hex ~ '^#[0-9a-fA-F]{6}$'),
  sort integer NOT NULL DEFAULT 100,
  UNIQUE (kunden_id, schluessel)
);
SELECT rls_kunde('shop_farben', true);

CREATE TABLE IF NOT EXISTS shop_produkte (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  schluessel text NOT NULL CHECK (schluessel ~ '^[a-z0-9][a-z0-9-]{0,60}$'),     -- die „id“ der Website, z. B. kuerbis-mini
  name text NOT NULL CHECK (length(name) BETWEEN 1 AND 120),
  kategorie text,                                                                -- Schlüssel einer Kategorie
  preis_cent integer NOT NULL CHECK (preis_cent BETWEEN 0 AND 10000000),
  kurz text NOT NULL DEFAULT '' CHECK (length(kurz) <= 400),
  lang text NOT NULL DEFAULT '' CHECK (length(lang) <= 4000),
  material text NOT NULL DEFAULT '' CHECK (length(material) <= 120),
  masse text NOT NULL DEFAULT '' CHECK (length(masse) <= 120),
  gewicht text NOT NULL DEFAULT '' CHECK (length(gewicht) <= 60),
  farben text[] NOT NULL DEFAULT '{}',
  tags text[] NOT NULL DEFAULT '{}',
  verwandt text[] NOT NULL DEFAULT '{}',
  personalisierbar boolean NOT NULL DEFAULT false,
  textlabel text CHECK (textlabel IS NULL OR length(textlabel) <= 80),
  textmax integer NOT NULL DEFAULT 0 CHECK (textmax BETWEEN 0 AND 200),
  sort integer NOT NULL DEFAULT 100,
  aktiv boolean NOT NULL DEFAULT false,                                          -- Entwurf, bis der Inhaber ihn aktiviert
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  geaendert_am timestamptz NOT NULL DEFAULT now(),
  UNIQUE (kunden_id, schluessel)
);
CREATE INDEX IF NOT EXISTS shop_produkte_idx ON shop_produkte (kunden_id, aktiv, sort);
SELECT rls_kunde('shop_produkte', true);
CREATE TRIGGER shop_produkte_geaendert BEFORE UPDATE ON shop_produkte FOR EACH ROW EXECUTE FUNCTION set_geaendert();

CREATE TABLE IF NOT EXISTS shop_bilder (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  produkt_id uuid NOT NULL REFERENCES shop_produkte(id) ON DELETE CASCADE,
  daten bytea NOT NULL,
  groesse integer NOT NULL,
  w integer NOT NULL, h integer NOT NULL,
  alt text NOT NULL DEFAULT '' CHECK (length(alt) <= 200),
  sort integer NOT NULL DEFAULT 100,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS shop_bilder_idx ON shop_bilder (produkt_id, sort, erstellt_am);
SELECT rls_kunde('shop_bilder', true);

CREATE TABLE IF NOT EXISTS shop_bestellungen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  ref text NOT NULL,
  nr integer NOT NULL,
  status text NOT NULL DEFAULT 'eingegangen' CHECK (status IN ('eingegangen','bestaetigt','bezahlt','im_druck','versendet','abholbereit','abgeholt','storniert')),
  name text NOT NULL, email text NOT NULL, telefon text,
  lieferart text NOT NULL CHECK (lieferart IN ('versand','abholung')),
  adresse jsonb,
  zahlungsart text NOT NULL CHECK (zahlungsart IN ('paypal','abholung')),
  zwischensumme_cent integer NOT NULL, versand_cent integer NOT NULL, summe_cent integer NOT NULL,
  anmerkung text,
  sendungsnummer text CHECK (sendungsnummer IS NULL OR length(sendungsnummer) <= 80),
  abholtermin text CHECK (abholtermin IS NULL OR length(abholtermin) <= 120),
  notiz text CHECK (notiz IS NULL OR length(notiz) <= 1000),
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  bezahlt_am timestamptz,
  UNIQUE (kunden_id, ref)
);
CREATE INDEX IF NOT EXISTS shop_bestellungen_idx ON shop_bestellungen (kunden_id, erstellt_am DESC);
SELECT rls_kunde('shop_bestellungen', true);

CREATE TABLE IF NOT EXISTS shop_positionen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  bestellung_id uuid NOT NULL REFERENCES shop_bestellungen(id) ON DELETE CASCADE,
  produkt_schluessel text NOT NULL,
  name text NOT NULL,
  farbe text, farbe_name text,
  wunschtext text,
  menge integer NOT NULL CHECK (menge BETWEEN 1 AND 99),
  einzelpreis_cent integer NOT NULL
);
CREATE INDEX IF NOT EXISTS shop_positionen_idx ON shop_positionen (bestellung_id);
SELECT rls_kunde('shop_positionen', true);
