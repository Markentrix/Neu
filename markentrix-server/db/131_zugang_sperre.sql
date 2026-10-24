-- Einzeln gesperrte Zugänge bleiben gesperrt, auch wenn der Kunde pausiert und wieder auf "aktiv" gesetzt wird.
ALTER TABLE benutzer ADD COLUMN IF NOT EXISTS gesperrt_manuell boolean NOT NULL DEFAULT false;
-- Bestand: ein gesperrter Zugang bei aktivem Kunden wurde von Hand gesperrt
UPDATE benutzer b SET gesperrt_manuell = true
 WHERE NOT b.aktiv AND b.kunden_id IS NOT NULL
   AND EXISTS (SELECT 1 FROM kunden k WHERE k.id = b.kunden_id AND k.status IN ('onboarding', 'aktiv'));
