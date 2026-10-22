-- Leads: Sperrliste verdrahten, Grundlage der Ansprache, Verlustgrund, Ergebnis-Code, stabiler Angebotslink
BEGIN;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ansprache_grundlage text CHECK (ansprache_grundlage IN ('anfrage','einwilligung','b2b_mutmasslich','empfehlung','bestandskontakt'));
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ansprache_hinweis text;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS verlust_grund text CHECK (verlust_grund IN ('kein_bedarf','zu_teuer','hat_anbieter','spaeter','falscher_ansprechpartner','sonstiges'));
ALTER TABLE lead_aktivitaeten ADD COLUMN IF NOT EXISTS ergebnis text;
ALTER TABLE belege ADD COLUMN IF NOT EXISTS annahme_token_enc text;
ALTER TABLE sperrliste DROP CONSTRAINT IF EXISTS sperrliste_grund_check;
ALTER TABLE sperrliste ADD CONSTRAINT sperrliste_grund_check CHECK (grund IN ('widerspruch','abmeldung','bounce','beschwerde','kunde','manuell','robinson','kein_interesse'));
-- alte Anrufe nachtragen, damit Auswertungen nicht mehr auf Textmuster angewiesen sind
UPDATE lead_aktivitaeten SET ergebnis='anruf_erreicht' WHERE ergebnis IS NULL AND art='anruf' AND inhalt LIKE 'Angerufen: erreicht%';
UPDATE lead_aktivitaeten SET ergebnis='anruf_nicht_erreicht' WHERE ergebnis IS NULL AND art='anruf' AND inhalt LIKE 'Angerufen: nicht erreicht%';
ALTER TABLE gespraechstermine ADD COLUMN IF NOT EXISTS erinnert_24 boolean NOT NULL DEFAULT false;
ALTER TABLE gespraechstermine ADD COLUMN IF NOT EXISTS erinnert_2 boolean NOT NULL DEFAULT false;
ALTER TABLE gespraechstermine ADD COLUMN IF NOT EXISTS gebucht_von text;
COMMIT;
