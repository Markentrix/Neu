-- 020 Konfiguration: Prompts, versionierte Einstellungen, Provisionsregeln. Eine Quelle für alle Workflows.
BEGIN;

CREATE TABLE konfiguration (
  id          bigserial PRIMARY KEY,
  schluessel  text NOT NULL,
  version     int  NOT NULL DEFAULT 1,
  wert        jsonb NOT NULL,
  status      text NOT NULL DEFAULT 'entwurf' CHECK (status IN ('entwurf','freigegeben','ersetzt')),
  beschreibung text NOT NULL DEFAULT '',
  freigegeben_von text,
  freigegeben_am  timestamptz,
  erstellt_am timestamptz NOT NULL DEFAULT now(),
  UNIQUE (schluessel, version)
);
CREATE VIEW v_konfiguration_aktuell WITH (security_invoker = true) AS
SELECT DISTINCT ON (schluessel) schluessel, version, wert, freigegeben_am
FROM konfiguration WHERE status = 'freigegeben' ORDER BY schluessel, version DESC;

CREATE TABLE prompts (
  id          bigserial PRIMARY KEY,
  agent       text NOT NULL,                -- z. B. email_agent, website_chat, telefon, angebots_ersteller
  kunden_id   uuid REFERENCES kunden(id) ON DELETE CASCADE,   -- NULL = Standard für alle Kunden
  version     int  NOT NULL DEFAULT 1,
  text        text NOT NULL,
  status      text NOT NULL DEFAULT 'entwurf' CHECK (status IN ('entwurf','freigegeben','ersetzt')),
  freigegeben_von text,
  freigegeben_am  timestamptz,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX prompts_version_uq ON prompts (agent, coalesce(kunden_id,'00000000-0000-0000-0000-000000000000'::uuid), version);

CREATE TABLE provisionsregeln (
  id            bigserial PRIMARY KEY,
  name          text NOT NULL,
  von_monat     int NOT NULL,               -- Vertragsmonat ab (1 = erster)
  bis_monat     int,                        -- NULL = offen
  prozent       numeric(5,2) NOT NULL CHECK (prozent >= 0 AND prozent <= 100),
  art           text NOT NULL DEFAULT 'laufend' CHECK (art IN ('laufend','verlaengerung','volumen','nachlauf','abloese')),
  status        text NOT NULL DEFAULT 'entwurf' CHECK (status IN ('entwurf','freigegeben','ersetzt')),
  quelle        text NOT NULL DEFAULT '',
  gueltig_ab    date,
  erstellt_am   timestamptz NOT NULL DEFAULT now()
);

SELECT rls_intern('konfiguration'); SELECT rls_intern('prompts'); SELECT rls_intern('provisionsregeln');

-- Provisionsstruktur laut Stand der Geschäftsentscheidung. Als ENTWURF, bis du sie freigibst.
INSERT INTO provisionsregeln (name,von_monat,bis_monat,prozent,art,quelle) VALUES
 ('Laufende Provision Monat 1–12',1,12,20,'laufend','Geschäftsentscheidung, noch nicht freigegeben'),
 ('Laufende Provision Monat 13–24',13,24,10,'laufend','Geschäftsentscheidung, noch nicht freigegeben'),
 ('Laufende Provision ab Monat 25',25,NULL,0,'laufend','Geschäftsentscheidung, noch nicht freigegeben'),
 ('Verlängerungsbonus',1,NULL,5,'verlaengerung','Geschäftsentscheidung, noch nicht freigegeben');

INSERT INTO konfiguration (schluessel,version,wert,status,beschreibung) VALUES
 ('provision.deckel_monate',1,'24','entwurf','Provision endet nach 24 Monaten'),
 ('provision.nachlauf_monate',1,'6','entwurf','Nachlauf nach Kündigung, danach Ablöse möglich'),
 ('oeffnungszeiten',1,'{"mo_do":"09:00-17:00","fr":"09:00-15:00","sa_so":"geschlossen"}','freigegeben','Öffnungszeiten Markentrix'),
 ('sprachregel.agent',1,'"Immer \"der Agent\" sagen, nie \"die KI\""','freigegeben','Sprachregel in Kundenkommunikation'),
 ('geschaeftsmodell',1,'"nur B2B, keine Verbraucher als Kunden oder Leads"','freigegeben','Grundregel');
COMMIT;
