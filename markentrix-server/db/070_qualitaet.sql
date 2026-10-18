-- 070 Qualität und Betrieb: Regelwerk, Prüfungen, Befunde, Maßnahmen, Ausnahmeregister,
-- Änderungsfreigaben, Alarme, Workflow-Fehler. Grundlage für ISO-9001-Ausrichtung.
BEGIN;

CREATE TABLE regeln (
  code text PRIMARY KEY, titel text NOT NULL, beschreibung text NOT NULL, dimension text, schwere text CHECK (schwere IN ('kritisch','wesentlich','kosmetisch')),
  aktiv boolean NOT NULL DEFAULT true, version int NOT NULL DEFAULT 1
);
SELECT rls_intern('regeln');

CREATE TABLE pruefungen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  modus text NOT NULL CHECK (modus IN ('voll','delta','maschine','fokus')), stand date NOT NULL DEFAULT current_date,
  ergebnis text CHECK (ergebnis IN ('go','go_mit_auflagen','no_go')), zusammenfassung text, erstellt_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('pruefungen');

CREATE TABLE befunde (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  pruefung_id uuid REFERENCES pruefungen(id) ON DELETE SET NULL,
  nummer int, titel text NOT NULL, beschreibung text, dimension text, regel_code text REFERENCES regeln(code),
  schwere text NOT NULL CHECK (schwere IN ('kritisch','wesentlich','kosmetisch')),
  status text NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','in_arbeit','behoben','verifiziert','ausnahme')),
  gefunden_am date NOT NULL DEFAULT current_date, erstellt_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('befunde');

CREATE TABLE massnahmen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  befund_id uuid NOT NULL REFERENCES befunde(id) ON DELETE CASCADE,
  beschreibung text NOT NULL, verantwortlich text, faellig_am date,
  status text NOT NULL DEFAULT 'geplant' CHECK (status IN ('geplant','in_arbeit','umgesetzt','verifiziert','verworfen')),
  verifiziert_von text, verifiziert_am timestamptz, nachweis text, erstellt_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('massnahmen');

-- Ausnahmeregister: Restrisiko wird nur formal akzeptiert, wenn es hier steht
CREATE TABLE ausnahmeregister (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  befund_id uuid REFERENCES befunde(id) ON DELETE SET NULL, regel_code text REFERENCES regeln(code),
  begruendung text NOT NULL, restrisiko text NOT NULL, kompensation text,
  akzeptiert_von text NOT NULL, akzeptiert_am date NOT NULL DEFAULT current_date, gueltig_bis date NOT NULL,
  status text NOT NULL DEFAULT 'aktiv' CHECK (status IN ('aktiv','abgelaufen','widerrufen'))
);
SELECT rls_intern('ausnahmeregister');

CREATE TABLE aenderungsfreigaben (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  gegenstand text NOT NULL, beschreibung text, art text CHECK (art IN ('preis','prompt','workflow','konfiguration','vertrag','sonstiges')),
  beantragt_von text, beantragt_am timestamptz NOT NULL DEFAULT now(),
  status text NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','freigegeben','abgelehnt','zurueckgezogen')),
  entschieden_von text, entschieden_am timestamptz, begruendung text
);
SELECT rls_intern('aenderungsfreigaben');

CREATE TABLE alarme (
  id bigserial PRIMARY KEY, zeit timestamptz NOT NULL DEFAULT now(),
  stufe text NOT NULL CHECK (stufe IN ('info','warnung','kritisch')), quelle text NOT NULL, titel text NOT NULL, details jsonb NOT NULL DEFAULT '{}'::jsonb,
  kanaele_gesendet text[] NOT NULL DEFAULT '{}',   -- mindestens zwei unabhängige Kanäle
  bestaetigt_von text, bestaetigt_am timestamptz
);
CREATE INDEX alarme_zeit_idx ON alarme (zeit DESC);
SELECT rls_intern('alarme');

CREATE TABLE workflow_fehler (
  id bigserial PRIMARY KEY, zeit timestamptz NOT NULL DEFAULT now(),
  workflow_id text, workflow_name text, knoten text, fehlertext text, kunden_id uuid REFERENCES kunden(id) ON DELETE SET NULL,
  gebuendelt_in bigint, behoben boolean NOT NULL DEFAULT false
);
CREATE INDEX workflow_fehler_zeit_idx ON workflow_fehler (zeit DESC);
SELECT rls_intern('workflow_fehler');
COMMIT;
