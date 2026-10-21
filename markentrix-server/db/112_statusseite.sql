-- Öffentliche Statusseite je Kunde (Link mit geheimem Kennzeichen, vom Kunden ein- und ausschaltbar)
BEGIN;
CREATE TABLE IF NOT EXISTS statusseiten (
  kunden_id uuid PRIMARY KEY REFERENCES kunden(id) ON DELETE CASCADE,
  token text NOT NULL UNIQUE,
  aktiv boolean NOT NULL DEFAULT false,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('statusseiten');
COMMIT;
