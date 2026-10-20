-- Freigaben: Versionen, Freigabe per Mail-Link ohne Login, Vorlagen; Vertretung beim Kunden
BEGIN;
ALTER TABLE kundenfreigaben ADD COLUMN IF NOT EXISTS version int NOT NULL DEFAULT 1;
ALTER TABLE kundenfreigaben ADD COLUMN IF NOT EXISTS vorgaenger_id uuid REFERENCES kundenfreigaben(id) ON DELETE SET NULL;
ALTER TABLE kundenfreigaben ADD COLUMN IF NOT EXISTS link_hash text;
ALTER TABLE kundenfreigaben ADD COLUMN IF NOT EXISTS link_ablauf timestamptz;
ALTER TABLE kundenfreigaben ADD COLUMN IF NOT EXISTS ueber_link boolean NOT NULL DEFAULT false;
CREATE UNIQUE INDEX IF NOT EXISTS kundenfreigaben_link_idx ON kundenfreigaben (link_hash) WHERE link_hash IS NOT NULL;

CREATE TABLE IF NOT EXISTS freigabe_vorlagen (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  art text NOT NULL CHECK (art IN ('social','text','angebot','design','website','sonstiges')),
  name text NOT NULL UNIQUE,
  titel text NOT NULL, inhalt text,
  erstellt_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('freigabe_vorlagen');
INSERT INTO freigabe_vorlagen (art, name, titel, inhalt) VALUES
 ('social', 'Social-Post Wochenangebot', 'Social-Post Wochenangebot KW ', E'Hallo,\n\nhier ist der Beitrag für das Wochenangebot zur Freigabe.\n\nText:\n\nBild/Grafik: siehe Anhang\n\nVeröffentlichung geplant am: '),
 ('social', 'Social-Post allgemein', 'Social-Post: ', E'Hallo,\n\nhier ist der Beitrag zur Freigabe.\n\nText:\n\nHashtags:\n\nVeröffentlichung geplant am: '),
 ('website', 'Website-Änderung', 'Website-Änderung: ', E'Hallo,\n\nwir haben folgende Änderung an Ihrer Website vorbereitet:\n\n- \n\nDie Änderung geht nach Ihrer Freigabe online.'),
 ('text', 'Newsletter-Text', 'Newsletter: ', E'Hallo,\n\nhier ist der Newsletter-Text zur Freigabe.\n\nBetreff:\n\nText:\n'),
 ('design', 'Design-Entwurf (Flyer, Anzeige)', 'Design-Entwurf: ', E'Hallo,\n\nanbei der Entwurf zur Freigabe (Datei im Anhang). Bitte prüfen Sie Texte, Preise, Telefonnummer und Öffnungszeiten besonders genau.')
ON CONFLICT (name) DO NOTHING;

ALTER TABLE kunden ADD COLUMN IF NOT EXISTS vertretung_email text;
ALTER TABLE kunden ADD COLUMN IF NOT EXISTS vertretung_name text;
ALTER TABLE kunden ADD COLUMN IF NOT EXISTS vertretung_von date;
ALTER TABLE kunden ADD COLUMN IF NOT EXISTS vertretung_bis date;
COMMIT;
