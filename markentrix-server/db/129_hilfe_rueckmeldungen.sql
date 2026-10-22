-- Rückmeldungen aus der Hilfe-Suche: war das Problem gelöst? Nicht gelöste Fragen gehen an den Admin.
CREATE TABLE hilfe_rueckmeldungen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  rolle text NOT NULL,                       -- vertrieb | kunde | admin
  benutzer_id uuid, kunden_id uuid, vertriebspartner_id uuid,
  name text, email text,
  frage text NOT NULL, artikel text,
  geloest boolean NOT NULL,
  text text,
  status text NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','erledigt')),
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  erledigt_am timestamptz
);
CREATE INDEX hilfe_rueckmeldungen_offen ON hilfe_rueckmeldungen (status, erstellt_am DESC);
SELECT rls_intern('hilfe_rueckmeldungen');
