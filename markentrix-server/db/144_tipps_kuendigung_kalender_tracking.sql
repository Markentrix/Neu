-- Kündigungsgrund (Auswahl), Hinweise auf weitere Pakete im Kundenportal, Kalender-Abo der Vertriebler, Conversion-Tracking auf Funnel-Seiten.

ALTER TABLE kuendigungswuensche ADD COLUMN IF NOT EXISTS grund_code text
  CHECK (grund_code IS NULL OR grund_code IN ('preis','nicht_genutzt','wenig_zeit','wechsel','betrieb_aufgegeben','leistung','sonstiges'));

CREATE TABLE kunden_tipps (
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  code text NOT NULL,
  status text NOT NULL DEFAULT 'gezeigt' CHECK (status IN ('gezeigt','interesse','nein')),
  geaendert_am timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (kunden_id, code)
);
SELECT rls_intern('kunden_tipps');

ALTER TABLE vertriebspartner ADD COLUMN IF NOT EXISTS kalender_token text UNIQUE;

ALTER TABLE lead_kampagnen ADD COLUMN IF NOT EXISTS meta_pixel_id text CHECK (meta_pixel_id IS NULL OR meta_pixel_id ~ '^[0-9]{8,20}$');
ALTER TABLE lead_kampagnen ADD COLUMN IF NOT EXISTS google_tag_id text CHECK (google_tag_id IS NULL OR google_tag_id ~ '^(G|AW|GT)-[A-Z0-9]{4,20}$');
ALTER TABLE lead_kampagnen ADD COLUMN IF NOT EXISTS google_lead_label text CHECK (google_lead_label IS NULL OR google_lead_label ~ '^AW-[0-9]+/[A-Za-z0-9_-]{6,40}$');
