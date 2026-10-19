-- Terminbuchung: Interessenten buchen ein Erstgespräch selbst
CREATE TABLE IF NOT EXISTS gespraechstermine (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  start timestamptz NOT NULL, ende timestamptz NOT NULL,
  name text NOT NULL, email text NOT NULL, telefon text, nachricht text,
  lead_id uuid REFERENCES leads(id) ON DELETE SET NULL,
  status text NOT NULL DEFAULT 'gebucht' CHECK (status IN ('gebucht','abgesagt')),
  token text NOT NULL UNIQUE, erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS gespraechstermine_start_uq ON gespraechstermine (start) WHERE status = 'gebucht';
SELECT rls_intern('gespraechstermine');
