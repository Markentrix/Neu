-- 060 Datenschutz und Recht: Einwilligungen, Auskunft, Löschung, Verarbeitungsverzeichnis, KI-Register.
BEGIN;

CREATE TABLE einwilligungen (
  id bigserial PRIMARY KEY,
  kunden_id uuid REFERENCES kunden(id) ON DELETE SET NULL,
  lead_id uuid REFERENCES leads(id) ON DELETE SET NULL,
  person_ref text NOT NULL,                  -- E-Mail oder Kennung der betroffenen Person
  zweck text NOT NULL,                       -- newsletter, leadverkauf, aufnahme, kontaktaufnahme ...
  erteilt boolean NOT NULL,
  textversion text NOT NULL,                 -- welcher Wortlaut wurde bestätigt
  nachweis jsonb NOT NULL DEFAULT '{}'::jsonb,   -- Zeit, IP-Hash, Klick-Ereignis
  zeit timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX einwilligungen_person_idx ON einwilligungen (lower(person_ref), zweck, zeit DESC);
SELECT rls_intern('einwilligungen');
ALTER TABLE leadverkauf ADD CONSTRAINT leadverkauf_einw_fk FOREIGN KEY (einwilligung_id) REFERENCES einwilligungen(id);

CREATE TABLE auskunftsanfragen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  person_ref text NOT NULL, art text NOT NULL DEFAULT 'auskunft' CHECK (art IN ('auskunft','berichtigung','loeschung','widerspruch','uebertragbarkeit')),
  eingang_am timestamptz NOT NULL DEFAULT now(),
  frist_bis date NOT NULL DEFAULT (current_date + 30),
  status text NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','in_bearbeitung','erledigt','abgelehnt')),
  erledigt_am timestamptz, notiz text
);
SELECT rls_intern('auskunftsanfragen');

CREATE TABLE loeschregeln (
  id serial PRIMARY KEY, tabelle text NOT NULL UNIQUE, aufbewahrung_tage int NOT NULL, grundlage text NOT NULL, aktiv boolean NOT NULL DEFAULT true
);
SELECT rls_intern('loeschregeln');

CREATE TABLE loeschprotokoll (          -- belegt, dass wirklich gelöscht wurde (nicht nur gezählt)
  id bigserial PRIMARY KEY, zeit timestamptz NOT NULL DEFAULT now(),
  tabelle text NOT NULL, regel_id int REFERENCES loeschregeln(id), geloescht_anzahl int NOT NULL, ausgeloest_durch text NOT NULL DEFAULT 'automatik'
);
SELECT rls_intern('loeschprotokoll');

CREATE TABLE verarbeitungsverzeichnis (
  id serial PRIMARY KEY, taetigkeit text NOT NULL UNIQUE, zweck text NOT NULL, kategorien_daten text NOT NULL, kategorien_personen text NOT NULL,
  empfaenger text, drittland text, rechtsgrundlage text NOT NULL, loeschfrist text, technische_massnahmen text,
  geprueft_am date, erstellt_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('verarbeitungsverzeichnis');

CREATE TABLE ki_register (
  id serial PRIMARY KEY, name text NOT NULL UNIQUE, zweck text NOT NULL, anbieter text, risikoklasse text,
  kennzeichnung text, menschliche_aufsicht text, kanal text, aktiv boolean NOT NULL DEFAULT true, geprueft_am date
);
SELECT rls_intern('ki_register');

INSERT INTO loeschregeln (tabelle,aufbewahrung_tage,grundlage) VALUES
 ('leads',365,'Tote Leads: Speicherbegrenzung, Löschfrist im Lead-Datensatz hat Vorrang'),
 ('lf_betriebe',180,'Lead-Finder-Rohdaten ohne Anbahnung'),
 ('akquise_antworten',365,'Dokumentation Akquise'),
 ('chat_verlauf',730,'Verlauf im Kundenbereich'),
 ('sitzungen',30,'Abgelaufene Sitzungen');
COMMIT;
