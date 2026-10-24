-- Preisänderung für ein Angebot, vom Vertriebler beantragt, vom Admin freigegeben oder abgelehnt
CREATE TABLE IF NOT EXISTS angebot_preisanfragen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  vertriebspartner_id uuid REFERENCES vertriebspartner(id) ON DELETE SET NULL,
  paket_code text NOT NULL,
  katalog jsonb NOT NULL,                       -- Katalogpreise zum Zeitpunkt der Anfrage (einrichtung_cent, monatlich_cent, projekt_cent)
  wunsch jsonb NOT NULL,                        -- gewünschte Preise
  nachlass_prozent numeric(5,2),
  begruendung text NOT NULL,
  status text NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','genehmigt','abgelehnt')),
  freigegeben jsonb,                            -- tatsächlich freigegebene Preise
  admin_notiz text,
  beleg_id uuid REFERENCES belege(id) ON DELETE SET NULL,
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  entschieden_am timestamptz,
  entschieden_von text
);
CREATE INDEX IF NOT EXISTS angebot_preisanfragen_lead ON angebot_preisanfragen (lead_id);
CREATE INDEX IF NOT EXISTS angebot_preisanfragen_status ON angebot_preisanfragen (status, erstellt_am DESC);
SELECT rls_intern('angebot_preisanfragen');
