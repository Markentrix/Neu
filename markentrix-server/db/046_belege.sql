-- Angebote, Rechnungen (inkl. Storno), Nummernkreise
CREATE TABLE IF NOT EXISTS nummernkreise (
  art     text NOT NULL,
  jahr    int  NOT NULL,
  zaehler int  NOT NULL DEFAULT 0,
  PRIMARY KEY (art, jahr)
);

CREATE TABLE IF NOT EXISTS belege (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  art           text NOT NULL CHECK (art IN ('angebot','rechnung')),
  nummer        text UNIQUE,                         -- erst beim Ausstellen vergeben, fortlaufend
  kunden_id     uuid NOT NULL REFERENCES kunden(id),
  status        text NOT NULL DEFAULT 'entwurf' CHECK (status IN ('entwurf','gestellt','versendet','angenommen','abgelehnt','bezahlt','storniert')),
  betreff       text NOT NULL DEFAULT '',
  einleitung    text NOT NULL DEFAULT '',
  schluss       text NOT NULL DEFAULT '',
  positionen    jsonb NOT NULL DEFAULT '[]'::jsonb,  -- [{text, menge, einheit, preis_cent}]
  leistungszeitraum text NOT NULL DEFAULT '',
  datum         date,                                -- Beleg-/Rechnungsdatum
  faellig_am    date,                                -- Rechnung: Zahlungsziel, Angebot: gültig bis
  netto_cent    bigint NOT NULL DEFAULT 0,
  ust_satz      numeric(5,2) NOT NULL DEFAULT 0,
  ust_cent      bigint NOT NULL DEFAULT 0,
  brutto_cent   bigint NOT NULL DEFAULT 0,
  kleinunternehmer boolean NOT NULL DEFAULT false,
  empfaenger    jsonb NOT NULL DEFAULT '{}'::jsonb,  -- Anschrift zum Zeitpunkt des Ausstellens
  angebot_id    uuid REFERENCES belege(id),
  storno_von    uuid REFERENCES belege(id),
  versendet_am  timestamptz,
  bezahlt_am    date,
  bezahlt_cent  bigint,
  mahnstufe     int NOT NULL DEFAULT 0,
  mahn_am       date,
  notiz         text,
  erstellt_am   timestamptz NOT NULL DEFAULT now(),
  geaendert_am  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS belege_kunde_idx ON belege (kunden_id, erstellt_am DESC);
CREATE INDEX IF NOT EXISTS belege_status_idx ON belege (art, status);
ALTER TABLE belege ENABLE ROW LEVEL SECURITY; ALTER TABLE belege FORCE ROW LEVEL SECURITY;
ALTER TABLE nummernkreise ENABLE ROW LEVEL SECURITY; ALTER TABLE nummernkreise FORCE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'belege' AND policyname = 'kunde_lesen') THEN
    CREATE POLICY kunde_lesen ON belege FOR SELECT USING (app_intern() OR (kunden_id = app_kunden_id() AND status <> 'entwurf'));
    CREATE POLICY intern_schreiben ON belege FOR ALL USING (app_intern()) WITH CHECK (app_intern());
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'nummernkreise') THEN
    CREATE POLICY intern ON nummernkreise FOR ALL USING (app_intern()) WITH CHECK (app_intern());
  END IF;
END $$;
