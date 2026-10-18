-- Texte, Events und Hinweise für die Angebotsseite der Kunden-Website, mehrsprachig.
BEGIN;

ALTER TABLE websites ADD COLUMN IF NOT EXISTS sprachen text[] NOT NULL DEFAULT '{de}';

CREATE TABLE angebots_inhalte (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  art text NOT NULL CHECK (art IN ('angebot','event','hinweis','geschlossen')),
  titel jsonb NOT NULL DEFAULT '{}',
  text jsonb NOT NULL DEFAULT '{}',
  preis text,
  gueltig_von date,
  gueltig_bis date,
  aktiv boolean NOT NULL DEFAULT true,
  erstellt_von uuid,
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  geaendert_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX angebots_inhalte_kunde_idx ON angebots_inhalte (kunden_id, aktiv);
SELECT rls_kunde('angebots_inhalte', true);

COMMIT;
