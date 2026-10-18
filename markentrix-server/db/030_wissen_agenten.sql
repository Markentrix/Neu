-- 030 Wissen und Agenten: Wissensbasis je Kunde, Agentenläufe, Freigaben (QA-Gate), Sperrlisten, Kosten.
BEGIN;

CREATE TABLE wissensbasis (
  id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id   uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  bereich     text NOT NULL,                -- z. B. leistungen, preise, oeffnungszeiten, faq, tonalitaet, einzugsgebiet
  schluessel  text NOT NULL,
  wert        text NOT NULL,
  quelle      text NOT NULL DEFAULT 'manuell',
  aktiv       boolean NOT NULL DEFAULT true,
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  geaendert_am timestamptz NOT NULL DEFAULT now(),
  UNIQUE (kunden_id, bereich, schluessel)
);
CREATE TRIGGER wissen_geaendert BEFORE UPDATE ON wissensbasis FOR EACH ROW EXECUTE FUNCTION set_geaendert();
SELECT rls_kunde('wissensbasis', true);

CREATE TABLE agent_laeufe (
  id            bigserial PRIMARY KEY,
  kunden_id     uuid REFERENCES kunden(id) ON DELETE SET NULL,
  agent         text NOT NULL,
  kanal         text,
  prompt_id     bigint REFERENCES prompts(id),
  eingabe_ref   text,                        -- Verweis, nicht der Volltext (Datenminimierung)
  ergebnis      text NOT NULL DEFAULT 'ok' CHECK (ergebnis IN ('ok','fehler','abgelehnt','zur_freigabe')),
  fehlertext    text,
  tokens_ein    int, tokens_aus int, kosten_cent numeric(10,2),
  dauer_ms      int,
  zeit          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX agent_laeufe_kunde_idx ON agent_laeufe (kunden_id, zeit DESC);
SELECT rls_kunde('agent_laeufe', false);

CREATE TABLE freigaben (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id     uuid REFERENCES kunden(id) ON DELETE CASCADE,
  art           text NOT NULL,               -- angebot, akquise_mail, social_post, gbp_post, preisaenderung ...
  bezug_tabelle text,
  bezug_id      text,
  vorschau      text,
  status        text NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','freigegeben','abgelehnt','abgelaufen')),
  entschieden_von text,
  entschieden_am  timestamptz,
  begruendung   text,
  erstellt_am   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX freigaben_offen_idx ON freigaben (status, erstellt_am);
SELECT rls_intern('freigaben');

-- Globale Sperrliste: niemand auf dieser Liste wird kontaktiert (Akquise, Lead-Finder, Verkauf)
CREATE TABLE sperrliste (
  id          bigserial PRIMARY KEY,
  art         text NOT NULL CHECK (art IN ('email','domain','telefon','firma','person')),
  wert        text NOT NULL,                 -- normalisiert (klein geschrieben, ohne Leerzeichen)
  grund       text NOT NULL CHECK (grund IN ('widerspruch','abmeldung','bounce','beschwerde','kunde','manuell','robinson')),
  quelle      text NOT NULL DEFAULT '',
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  UNIQUE (art, wert)
);
SELECT rls_intern('sperrliste');

CREATE TABLE kosten_log (
  id          bigserial PRIMARY KEY,
  zeit        timestamptz NOT NULL DEFAULT now(),
  kunden_id   uuid REFERENCES kunden(id) ON DELETE SET NULL,
  dienst      text NOT NULL,                 -- anthropic, retell, google_places, pagespeed, ...
  einheit     text,
  menge       numeric,
  kosten_cent numeric(12,4) NOT NULL DEFAULT 0
);
CREATE INDEX kosten_zeit_idx ON kosten_log (zeit DESC);
SELECT rls_intern('kosten_log');
COMMIT;
