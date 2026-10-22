-- Kunden schlagen Änderungen an ihrer Wissensbasis vor, das Team prüft und übernimmt. Dazu: Erinnerung bei offenen Gutscheinen.
BEGIN;
CREATE TABLE IF NOT EXISTS wissen_vorschlaege (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  wissen_id uuid REFERENCES wissensbasis(id) ON DELETE SET NULL,
  aktion text NOT NULL CHECK (aktion IN ('neu','aendern','ausschalten')),
  bereich text, schluessel text NOT NULL, wert text,
  status text NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','uebernommen','abgelehnt','zurueckgezogen')),
  notiz text,
  von uuid, erstellt_am timestamptz NOT NULL DEFAULT now(), bearbeitet_am timestamptz
);
CREATE INDEX IF NOT EXISTS wissen_vorschlaege_idx ON wissen_vorschlaege (kunden_id, status, erstellt_am DESC);
SELECT rls_kunde('wissen_vorschlaege', true);
ALTER TABLE website_gutscheine ADD COLUMN IF NOT EXISTS erinnert_am timestamptz;
COMMIT;
