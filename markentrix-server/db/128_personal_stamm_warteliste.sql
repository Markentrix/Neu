-- Zugang eines Mitarbeiters ist mit einer Person der Terminbuchung verknüpft (sieht dann nur deren Termine).
ALTER TABLE benutzer ADD COLUMN IF NOT EXISTS website_mitarbeiter_id uuid REFERENCES website_mitarbeiter(id) ON DELETE SET NULL;

-- Notizen zu Stammkunden (Schlüssel: kleingeschriebene E-Mail oder 'tel:' plus Ziffern)
CREATE TABLE IF NOT EXISTS website_stamm_notizen (
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  schluessel text NOT NULL,
  notiz text NOT NULL,
  geaendert_am timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (kunden_id, schluessel)
);
SELECT rls_intern('website_stamm_notizen');

-- „Ich komme“: der Besucher bestätigt seinen Termin per Klick in der Erinnerung
ALTER TABLE website_termine ADD COLUMN IF NOT EXISTS kommt_am timestamptz;

-- Warteliste für ausgebuchte Tage
CREATE TABLE IF NOT EXISTS website_warteliste (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  ref text, name text NOT NULL, email text NOT NULL, telefon text,
  tag date NOT NULL,
  leistung_id uuid REFERENCES website_leistungen(id) ON DELETE SET NULL,
  mitarbeiter_id uuid REFERENCES website_mitarbeiter(id) ON DELETE SET NULL,
  status text NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','benachrichtigt','erledigt')),
  benachrichtigt_am timestamptz,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS website_warteliste_tag ON website_warteliste (kunden_id, tag, status);
SELECT rls_intern('website_warteliste');
