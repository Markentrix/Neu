-- Zahlung per Stripe, Anrufprotokoll, Branchenvorlagen, Push-Nachrichten, Job-Marker
ALTER TABLE belege ADD COLUMN IF NOT EXISTS zahlart text;          -- ueberweisung | lastschrift
ALTER TABLE belege ADD COLUMN IF NOT EXISTS einzug_am date;        -- Datum des angekündigten Lastschrift-Einzugs
ALTER TABLE belege ADD COLUMN IF NOT EXISTS auto_gemahnt_am date;

CREATE TABLE IF NOT EXISTS sepa_mandate (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  referenz text NOT NULL UNIQUE,
  kontoinhaber text NOT NULL,
  iban_verschluesselt text NOT NULL, iban_ende text NOT NULL, bic text,
  erteilt_am timestamptz NOT NULL DEFAULT now(), erteilt_ip text,
  widerrufen_am timestamptz,
  erstmals_genutzt boolean NOT NULL DEFAULT false
);
CREATE UNIQUE INDEX IF NOT EXISTS sepa_mandate_aktiv_uq ON sepa_mandate (kunden_id) WHERE widerrufen_am IS NULL;
SELECT rls_kunde('sepa_mandate', false);

ALTER TABLE anrufe ADD COLUMN IF NOT EXISTS name text;
ALTER TABLE anrufe ADD COLUMN IF NOT EXISTS anfrage_id uuid REFERENCES anfragen(id) ON DELETE SET NULL;
CREATE UNIQUE INDEX IF NOT EXISTS anrufe_extern_uq ON anrufe (kunden_id, extern_ref) WHERE extern_ref IS NOT NULL;

ALTER TABLE kunden ADD COLUMN IF NOT EXISTS vorlage text;
ALTER TABLE kunden ADD COLUMN IF NOT EXISTS vorlage_am timestamptz;

CREATE TABLE IF NOT EXISTS push_abos (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  benutzer_id uuid NOT NULL REFERENCES benutzer(id) ON DELETE CASCADE,
  endpoint text NOT NULL UNIQUE,
  p256dh text NOT NULL, auth text NOT NULL,
  geraet text, fehler int NOT NULL DEFAULT 0,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS push_abos_benutzer_idx ON push_abos (benutzer_id);
SELECT rls_intern('push_abos');

CREATE TABLE IF NOT EXISTS job_marker (
  schluessel text PRIMARY KEY, am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('job_marker');
