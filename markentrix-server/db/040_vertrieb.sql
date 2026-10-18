-- 040 Vertrieb: Vertriebspartner, Provisionen, Leads, Akquise, Leadverkauf, Lead-Finder (lf_*).
-- Alles intern. Markentrix arbeitet nur im B2B.
BEGIN;

CREATE TABLE vertriebspartner (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL, firma text, email text, telefon text,
  status text NOT NULL DEFAULT 'aktiv' CHECK (status IN ('anfrage','aktiv','pausiert','beendet')),
  vereinbarung_am date, iban_hinterlegt boolean NOT NULL DEFAULT false,
  notiz text, erstellt_am timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE kunden ADD CONSTRAINT kunden_partner_fk FOREIGN KEY (vertriebspartner_id) REFERENCES vertriebspartner(id) ON DELETE SET NULL;
SELECT rls_intern('vertriebspartner');

CREATE TABLE provisionen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  vertriebspartner_id uuid NOT NULL REFERENCES vertriebspartner(id),
  kunden_id uuid NOT NULL REFERENCES kunden(id),
  buchung_id uuid REFERENCES buchungen(id),
  regel_id bigint REFERENCES provisionsregeln(id),
  monat date NOT NULL,                      -- erster Tag des Abrechnungsmonats
  vertragsmonat int NOT NULL,
  basis_cent bigint NOT NULL, prozent numeric(5,2) NOT NULL, betrag_cent bigint NOT NULL,
  status text NOT NULL DEFAULT 'berechnet' CHECK (status IN ('berechnet','freigegeben','ausgezahlt','storniert')),
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  UNIQUE (vertriebspartner_id, buchung_id, monat)
);
SELECT rls_intern('provisionen');

CREATE TABLE leads (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  firma text NOT NULL, ansprechpartner text, email text, telefon text, website text,
  branche text, plz text, ort text,
  quelle text NOT NULL DEFAULT 'manuell' CHECK (quelle IN ('manuell','lead_finder','empfehlung','website','akquise','messe')),
  status text NOT NULL DEFAULT 'neu' CHECK (status IN ('neu','kontaktiert','antwort','termin','angebot','gewonnen','verloren','gesperrt','consent_ausstehend','tot')),
  score int, kunden_id uuid REFERENCES kunden(id) ON DELETE SET NULL,
  vertriebspartner_id uuid REFERENCES vertriebspartner(id) ON DELETE SET NULL,
  loeschen_nach date,                       -- Speicherbegrenzung, tote Leads werden nicht ewig geführt
  notiz text, erstellt_am timestamptz NOT NULL DEFAULT now(), geaendert_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX leads_status_idx ON leads (status);
CREATE INDEX leads_loeschen_idx ON leads (loeschen_nach) WHERE loeschen_nach IS NOT NULL;
CREATE TRIGGER leads_geaendert BEFORE UPDATE ON leads FOR EACH ROW EXECUTE FUNCTION set_geaendert();
SELECT rls_intern('leads');

CREATE TABLE lead_aktivitaeten (
  id bigserial PRIMARY KEY,
  lead_id uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  art text NOT NULL CHECK (art IN ('mail_gesendet','antwort','anruf','termin','notiz','statuswechsel','consent')),
  inhalt text, zeit timestamptz NOT NULL DEFAULT now(), von text
);
CREATE INDEX lead_akt_idx ON lead_aktivitaeten (lead_id, zeit DESC);
SELECT rls_intern('lead_aktivitaeten');

CREATE TABLE akquise_kampagnen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL, zielgruppe text, vorlage_prompt_id bigint REFERENCES prompts(id),
  status text NOT NULL DEFAULT 'entwurf' CHECK (status IN ('entwurf','rechtlich_geprueft','aktiv','pausiert','beendet')),
  rechtlich_geprueft_am date, tagesgrenze int NOT NULL DEFAULT 0,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('akquise_kampagnen');

CREATE TABLE akquise_versand (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kampagne_id uuid NOT NULL REFERENCES akquise_kampagnen(id),
  lead_id uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  freigabe_id uuid REFERENCES freigaben(id),
  betreff text, text text,
  status text NOT NULL DEFAULT 'entwurf' CHECK (status IN ('entwurf','zur_freigabe','freigegeben','gesendet','fehler','bounce')),
  gesendet_am timestamptz, erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX akquise_versand_lead_idx ON akquise_versand (lead_id);
SELECT rls_intern('akquise_versand');

CREATE TABLE akquise_antworten (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  versand_id uuid REFERENCES akquise_versand(id) ON DELETE SET NULL,
  lead_id uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  text text, klassifizierung text CHECK (klassifizierung IN ('interessiert','kein_interesse','widerspruch','abwesend','unklar')),
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('akquise_antworten');

-- Verkauf qualifizierter Leads an externe Vertriebler: nur mit Opt-in des Leads
CREATE TABLE leadverkauf (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id uuid NOT NULL REFERENCES leads(id),
  einwilligung_id bigint,                   -- Verweis auf einwilligungen (060)
  empfaenger text, preis_cent bigint,
  status text NOT NULL DEFAULT 'consent_ausstehend' CHECK (status IN ('consent_ausstehend','bereit','zugestellt','abgerechnet','abgebrochen')),
  zugestellt_am timestamptz, erstellt_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('leadverkauf');

-- Lead-Finder (erstes fachliches Modul von markentrix-core) -------------------------
CREATE TABLE lf_branchen_mapping (
  id serial PRIMARY KEY, branche text NOT NULL, google_typ text NOT NULL, aktiv boolean NOT NULL DEFAULT true,
  UNIQUE (branche, google_typ)
);
SELECT rls_intern('lf_branchen_mapping');

CREATE TABLE lf_budget (
  id serial PRIMARY KEY, dienst text NOT NULL, monat date NOT NULL, limit_cent bigint NOT NULL, verbraucht_cent bigint NOT NULL DEFAULT 0,
  UNIQUE (dienst, monat)
);
SELECT rls_intern('lf_budget');

CREATE TABLE lf_suchlaeufe (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  plz text, ort text, umkreis_km int, branchen text[], quelle text NOT NULL DEFAULT 'google_places',
  status text NOT NULL DEFAULT 'angelegt' CHECK (status IN ('angelegt','laeuft','fertig','fehler','abgebrochen')),
  treffer int, kosten_cent numeric(12,4) NOT NULL DEFAULT 0, fehlertext text,
  gestartet_am timestamptz NOT NULL DEFAULT now(), beendet_am timestamptz
);
SELECT rls_intern('lf_suchlaeufe');

CREATE TABLE lf_betriebe (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  suchlauf_id uuid REFERENCES lf_suchlaeufe(id) ON DELETE SET NULL,
  place_id text UNIQUE, name text NOT NULL, branche text, adresse text, plz text, ort text,
  lat double precision, lng double precision, telefon text, website text,
  website_art text CHECK (website_art IN ('keine','nur_social','eigene','plattform','konzern')),
  geschaeftsstatus text, bewertung numeric(2,1), bewertungen_anzahl int,
  lead_id uuid REFERENCES leads(id) ON DELETE SET NULL,
  erstellt_am timestamptz NOT NULL DEFAULT now(), geaendert_am timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX lf_betriebe_plz_idx ON lf_betriebe (plz);
SELECT rls_intern('lf_betriebe');

CREATE TABLE lf_kontakte (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  betrieb_id uuid NOT NULL REFERENCES lf_betriebe(id) ON DELETE CASCADE,
  name text, rolle text, email text, telefon text, quelle text, erstellt_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('lf_kontakte');

CREATE TABLE lf_website_pruefung (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  betrieb_id uuid NOT NULL REFERENCES lf_betriebe(id) ON DELETE CASCADE,
  geprueft_am timestamptz NOT NULL DEFAULT now(), quelle text NOT NULL DEFAULT 'pagespeed',
  performance int, seo int, barrierefreiheit int, mobil_tauglich boolean, https boolean,
  lauffehler text, redesign_prioritaet text CHECK (redesign_prioritaet IN ('hoch','mittel','niedrig','unklar')),
  rohdaten jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX lf_pruefung_betrieb_idx ON lf_website_pruefung (betrieb_id, geprueft_am DESC);
SELECT rls_intern('lf_website_pruefung');

CREATE TABLE lf_signale (
  id bigserial PRIMARY KEY, betrieb_id uuid NOT NULL REFERENCES lf_betriebe(id) ON DELETE CASCADE,
  art text NOT NULL, wert text, erfasst_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('lf_signale');

CREATE TABLE lf_scores (
  id bigserial PRIMARY KEY, betrieb_id uuid NOT NULL REFERENCES lf_betriebe(id) ON DELETE CASCADE,
  score int NOT NULL, begruendung jsonb NOT NULL DEFAULT '{}'::jsonb, version text, berechnet_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('lf_scores');

CREATE TABLE lf_outreach (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  betrieb_id uuid NOT NULL REFERENCES lf_betriebe(id) ON DELETE CASCADE,
  kanal text NOT NULL CHECK (kanal IN ('email','brief','telefon','persoenlich')),
  status text NOT NULL DEFAULT 'geplant' CHECK (status IN ('geplant','zur_freigabe','gesendet','antwort','abgelehnt','gesperrt')),
  freigabe_id uuid REFERENCES freigaben(id), text text, erstellt_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('lf_outreach');
COMMIT;
