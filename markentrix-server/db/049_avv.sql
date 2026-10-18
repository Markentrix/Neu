-- Auftragsverarbeitungsverträge (AVV) pro Kunde: erzeugte Verträge und unterschriebene Ablage
CREATE TABLE IF NOT EXISTS avv (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id        uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  version          text NOT NULL,
  erstellt_am      timestamptz NOT NULL DEFAULT now(),
  gesendet_am      timestamptz,
  unterschrieben_am date,
  datei            bytea,
  datei_name       text,
  datei_typ        text,
  hochgeladen_am   timestamptz
);
CREATE INDEX IF NOT EXISTS avv_kunde_idx ON avv (kunden_id, erstellt_am DESC);
ALTER TABLE avv ENABLE ROW LEVEL SECURITY; ALTER TABLE avv FORCE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'avv') THEN
    CREATE POLICY kunde_lesen ON avv FOR SELECT USING (app_intern() OR (kunden_id = app_kunden_id() AND datei IS NOT NULL));
    CREATE POLICY intern_schreiben ON avv FOR ALL USING (app_intern()) WITH CHECK (app_intern());
  END IF;
END $$;
ALTER TABLE kunden ADD COLUMN IF NOT EXISTS avv_erinnert_am timestamptz;
