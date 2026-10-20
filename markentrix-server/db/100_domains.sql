-- Domainverwaltung pro Kunde (Inhaber, Ablauf, Kosten). Auth-Codes werden bewusst nicht gespeichert.
BEGIN;
CREATE TABLE IF NOT EXISTS domains (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kunden_id uuid NOT NULL REFERENCES kunden(id) ON DELETE CASCADE,
  domain text NOT NULL,
  registrar text NOT NULL DEFAULT 'INWX',
  inhaber text NOT NULL DEFAULT 'markentrix' CHECK (inhaber IN ('kunde','markentrix')),
  inhaber_name text, inhaber_kontakt text,
  registriert_am date, ablauf_am date,
  auto_verlaengern boolean NOT NULL DEFAULT true,
  preis_jahr_cent int CHECK (preis_jahr_cent IS NULL OR preis_jahr_cent >= 0),
  status text NOT NULL DEFAULT 'aktiv' CHECK (status IN ('aktiv','transfer','gekuendigt')),
  notiz text,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS domains_eindeutig ON domains (kunden_id, lower(domain));
CREATE INDEX IF NOT EXISTS domains_ablauf_idx ON domains (ablauf_am) WHERE status = 'aktiv';
SELECT rls_intern('domains');
COMMIT;
