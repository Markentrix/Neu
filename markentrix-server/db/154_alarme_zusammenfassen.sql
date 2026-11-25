-- Alarme: gleiche Meldung nur einmal, mit Zähler. Behobene Alarme schließen sich selbst.
ALTER TABLE alarme ADD COLUMN IF NOT EXISTS schluessel text;
ALTER TABLE alarme ADD COLUMN IF NOT EXISTS anzahl integer NOT NULL DEFAULT 1;
ALTER TABLE alarme ADD COLUMN IF NOT EXISTS zuletzt timestamptz;
UPDATE alarme SET zuletzt = zeit WHERE zuletzt IS NULL;
CREATE INDEX IF NOT EXISTS alarme_offen_idx ON alarme (schluessel) WHERE bestaetigt_am IS NULL;

-- Bisher offene Alarme mit gleicher Quelle, gleichem Titel und gleicher Meldung zu einem zusammenfassen (der älteste bleibt, der Zähler zählt mit)
WITH g AS (
  SELECT quelle, titel, COALESCE(details->>'text', '') AS txt, min(id) AS behalten, count(*) AS n, min(zeit) AS erste, max(zeit) AS letzte
  FROM alarme WHERE bestaetigt_am IS NULL GROUP BY 1, 2, 3 HAVING count(*) > 1
), u AS (
  UPDATE alarme a SET anzahl = g.n, zeit = g.erste, zuletzt = g.letzte,
         schluessel = a.quelle || '|' || a.titel || '|' || md5(g.txt)
  FROM g WHERE a.id = g.behalten RETURNING a.id
)
DELETE FROM alarme a USING g
WHERE a.bestaetigt_am IS NULL AND a.quelle = g.quelle AND a.titel = g.titel AND COALESCE(a.details->>'text', '') = g.txt AND a.id <> g.behalten;
UPDATE alarme SET schluessel = quelle || '|' || titel || '|' || md5(COALESCE(details->>'text', '')) WHERE schluessel IS NULL AND bestaetigt_am IS NULL;
