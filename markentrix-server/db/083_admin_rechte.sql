-- Mitarbeiter im Admin-Bereich mit eingeschränkten Rechten (NULL = voller Zugriff)
ALTER TABLE benutzer ADD COLUMN IF NOT EXISTS admin_rechte text[];
