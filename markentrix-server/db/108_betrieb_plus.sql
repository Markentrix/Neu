-- Mail-Zustellbarkeit, Kündigungswünsche
BEGIN;
CREATE TABLE IF NOT EXISTS mail_protokoll (
  id bigserial PRIMARY KEY,
  zeit timestamptz NOT NULL DEFAULT now(),
  kunden_id uuid REFERENCES kunden(id) ON DELETE CASCADE,
  art text NOT NULL DEFAULT 'system',
  an_domain text,                        -- bewusst nur die Domain des Empfängers, keine Adresse
  ok boolean NOT NULL,
  fehlerart text,                        -- adresse | anmeldung | verbindung | sonstiges
  fehler text
);
CREATE INDEX IF NOT EXISTS mail_protokoll_zeit_idx ON mail_protokoll (zeit DESC);
CREATE INDEX IF NOT EXISTS mail_protokoll_kunde_idx ON mail_protokoll (kunden_id, zeit DESC) WHERE kunden_id IS NOT NULL;
SELECT rls_intern('mail_protokoll');

CREATE TABLE IF NOT EXISTS mail_dns (
  domain text PRIMARY KEY,
  geprueft_am timestamptz NOT NULL DEFAULT now(),
  spf text NOT NULL, dkim text NOT NULL, dmarc text NOT NULL,   -- ok | warn | fehlt | unbekannt
  details jsonb NOT NULL DEFAULT '{}'::jsonb
);
SELECT rls_intern('mail_dns');

CREATE TABLE IF NOT EXISTS kuendigungswuensche (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  grund text, wunschdatum date,
  von_name text, von_email text,
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  status text NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','bearbeitet','zurueckgenommen')),
  bearbeitet_am timestamptz
);
CREATE INDEX IF NOT EXISTS kuendigungswuensche_kunde_idx ON kuendigungswuensche (kunden_id, erstellt_am DESC);
SELECT rls_intern('kuendigungswuensche');
COMMIT;
