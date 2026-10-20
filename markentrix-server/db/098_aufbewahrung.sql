-- Aufbewahrung wie im AVV (Version 2, Anlage 2): Chatverläufe 6 Monate, Audit-Log 12 Monate
BEGIN;
UPDATE loeschregeln SET aufbewahrung_tage = 180, grundlage = 'Verlauf im Kundenbereich (laut AVV 6 Monate)' WHERE tabelle = 'chat_verlauf' AND aufbewahrung_tage = 730;
INSERT INTO loeschregeln (tabelle, aufbewahrung_tage, grundlage) VALUES ('audit_log', 365, 'Protokoll wesentlicher Aktionen (laut AVV 12 Monate)') ON CONFLICT (tabelle) DO NOTHING;

-- Das Audit-Log bleibt für die Anwendung unveränderlich (kein UPDATE/DELETE für mk_app).
-- Nur diese Funktion darf Einträge löschen, und ausschließlich solche, die älter als 12 Monate sind.
CREATE OR REPLACE FUNCTION audit_aufraeumen() RETURNS int LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, pg_temp AS $$
DECLARE n int;
BEGIN
  DELETE FROM audit_log WHERE zeit < now() - interval '12 months';
  GET DIAGNOSTICS n = ROW_COUNT;
  RETURN n;
END $$;
REVOKE ALL ON FUNCTION audit_aufraeumen() FROM PUBLIC;
DO $$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mk_app') THEN GRANT EXECUTE ON FUNCTION audit_aufraeumen() TO mk_app; END IF; END $$;
COMMIT;
