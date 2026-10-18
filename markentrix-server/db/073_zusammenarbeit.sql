-- 073 Zusammenarbeit: Nachrichten und Aufträge (Tickets), Dateien/Dokumente, Kundenfreigaben, Aufgaben, Zufriedenheit.
-- (kundenfreigaben = Freigaben durch den Kunden; die Tabelle 'freigaben' aus 030 sind interne Agenten-Freigaben.)
BEGIN;

ALTER TABLE kunden ADD COLUMN IF NOT EXISTS benachr_nachrichten boolean NOT NULL DEFAULT true;

CREATE SEQUENCE IF NOT EXISTS ticket_nr_seq;
CREATE TABLE tickets (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  nummer bigint NOT NULL DEFAULT nextval('ticket_nr_seq'),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  betreff text NOT NULL CHECK (length(betreff) BETWEEN 1 AND 200),
  art text NOT NULL DEFAULT 'frage' CHECK (art IN ('frage','auftrag','aenderung','problem','modul')),
  status text NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','in_arbeit','wartet_auf_kunde','erledigt')),
  prioritaet text NOT NULL DEFAULT 'normal' CHECK (prioritaet IN ('normal','hoch')),
  modul_code text,
  erstellt_von uuid REFERENCES benutzer(id) ON DELETE SET NULL,
  ersteller_name text,
  zustaendig text,
  faellig_am date,
  letzte_nachricht_von text NOT NULL DEFAULT 'kunde' CHECK (letzte_nachricht_von IN ('kunde','team')),
  kunde_ungelesen boolean NOT NULL DEFAULT false,
  team_ungelesen boolean NOT NULL DEFAULT true,
  erste_antwort_am timestamptz,
  erledigt_am timestamptz,
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  geaendert_am timestamptz NOT NULL DEFAULT now(),
  erinnert_am timestamptz
);
CREATE INDEX tickets_kunde_idx ON tickets (kunden_id, geaendert_am DESC);
CREATE INDEX tickets_status_idx ON tickets (status, geaendert_am DESC);
SELECT rls_kunde('tickets', true);

CREATE TABLE ticket_nachrichten (
  id bigserial PRIMARY KEY,
  ticket_id uuid NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  von text NOT NULL CHECK (von IN ('kunde','team')),
  autor_name text,
  intern boolean NOT NULL DEFAULT false,        -- interne Notiz, der Kunde sieht sie nicht
  text text NOT NULL CHECK (length(text) BETWEEN 1 AND 10000),
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ticket_nachrichten_idx ON ticket_nachrichten (ticket_id, id);
ALTER TABLE ticket_nachrichten ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticket_nachrichten FORCE ROW LEVEL SECURITY;
CREATE POLICY trennung ON ticket_nachrichten
  USING (app_intern() OR (kunden_id = app_kunden_id() AND NOT intern))
  WITH CHECK (app_intern() OR (kunden_id = app_kunden_id() AND NOT intern AND von = 'kunde'));

CREATE TABLE kundenfreigaben (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  titel text NOT NULL CHECK (length(titel) BETWEEN 1 AND 200),
  art text NOT NULL DEFAULT 'sonstiges' CHECK (art IN ('social','text','angebot','design','website','sonstiges')),
  inhalt text,
  status text NOT NULL DEFAULT 'wartet' CHECK (status IN ('wartet','freigegeben','abgelehnt','zurueckgezogen')),
  angefragt_von text,
  angefragt_am timestamptz NOT NULL DEFAULT now(),
  entschieden_am timestamptz,
  entschieden_von uuid REFERENCES benutzer(id) ON DELETE SET NULL,
  entschieden_name text,
  entschieden_ip text,
  kommentar text,
  erinnert_am timestamptz
);
CREATE INDEX kundenfreigaben_kunde_idx ON kundenfreigaben (kunden_id, angefragt_am DESC);
SELECT rls_kunde('kundenfreigaben', true);

CREATE TABLE dateien (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  ticket_id uuid REFERENCES tickets(id) ON DELETE CASCADE,
  freigabe_id uuid REFERENCES kundenfreigaben(id) ON DELETE CASCADE,
  bereich text NOT NULL CHECK (bereich IN ('anhang','dokument')),
  kategorie text,                                -- nur bei Dokumenten
  name text NOT NULL,
  mime text NOT NULL,
  groesse bigint NOT NULL CHECK (groesse > 0 AND groesse <= 8388608),
  daten bytea NOT NULL,
  von text NOT NULL CHECK (von IN ('kunde','team')),
  hochgeladen_von uuid REFERENCES benutzer(id) ON DELETE SET NULL,
  sichtbar_kunde boolean NOT NULL DEFAULT true,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX dateien_kunde_idx ON dateien (kunden_id, bereich, erstellt_am DESC);
CREATE INDEX dateien_ticket_idx ON dateien (ticket_id) WHERE ticket_id IS NOT NULL;
ALTER TABLE dateien ENABLE ROW LEVEL SECURITY;
ALTER TABLE dateien FORCE ROW LEVEL SECURITY;
CREATE POLICY trennung ON dateien
  USING (app_intern() OR (kunden_id = app_kunden_id() AND sichtbar_kunde))
  WITH CHECK (app_intern() OR (kunden_id = app_kunden_id() AND sichtbar_kunde AND von = 'kunde'));

CREATE TABLE aufgaben (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid REFERENCES kunden(id) ON DELETE CASCADE,
  titel text NOT NULL CHECK (length(titel) BETWEEN 1 AND 200),
  beschreibung text,
  zustaendig text,
  faellig_am date,
  status text NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','erledigt')),
  quelle text NOT NULL DEFAULT 'manuell' CHECK (quelle IN ('manuell','auto')),
  auto_schluessel text UNIQUE,
  ticket_id uuid REFERENCES tickets(id) ON DELETE SET NULL,
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  erledigt_am timestamptz,
  erledigt_von text
);
CREATE INDEX aufgaben_status_idx ON aufgaben (status, faellig_am);
SELECT rls_intern('aufgaben');

CREATE TABLE zufriedenheit (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  ticket_id uuid REFERENCES tickets(id) ON DELETE SET NULL,
  art text NOT NULL CHECK (art IN ('ticket','quartal')),
  punkte smallint NOT NULL CHECK (punkte BETWEEN 0 AND 10),
  kommentar text,
  benutzer_id uuid REFERENCES benutzer(id) ON DELETE SET NULL,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX zufriedenheit_idx ON zufriedenheit (kunden_id, erstellt_am DESC);
CREATE UNIQUE INDEX zufriedenheit_ticket_uni ON zufriedenheit (ticket_id) WHERE ticket_id IS NOT NULL;
SELECT rls_kunde('zufriedenheit', true);

COMMIT;
