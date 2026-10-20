-- Ankündigung von Änderungen bei Unterauftragsverarbeitern (AVV Ziff. 5 Abs. 2: mindestens vier Wochen vorher, Widerspruch möglich)
BEGIN;
CREATE TABLE IF NOT EXISTS uav_aenderungen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  art text NOT NULL CHECK (art IN ('neu','ersetzt')),
  name text NOT NULL, leistung text NOT NULL, modul text, ort text,
  wirksam_ab date NOT NULL, hinweis text,
  erstellt_am timestamptz NOT NULL DEFAULT now(), erstellt_von uuid
);
SELECT rls_intern('uav_aenderungen');
CREATE TABLE IF NOT EXISTS uav_mitteilungen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  aenderung_id uuid NOT NULL REFERENCES uav_aenderungen(id) ON DELETE CASCADE,
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  email text, gesendet_am timestamptz,
  widerspruch_am timestamptz, widerspruch_grund text, widerspruch_von text,
  UNIQUE (aenderung_id, kunden_id)
);
SELECT rls_kunde('uav_mitteilungen', false);
COMMIT;
