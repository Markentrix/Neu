-- Digitale Visitenkarte (nur für Markentrix selbst: Admins und Vertriebler), wird als .vcf-Datei verschickt
CREATE TABLE visitenkarten (
  benutzer_id  uuid PRIMARY KEY REFERENCES benutzer(id) ON DELETE CASCADE,
  anzeigename  text,
  funktion     text,
  telefon      text,
  mobil        text,
  email        text,
  web          text,
  geaendert_am timestamptz NOT NULL DEFAULT now()
);
SELECT rls_intern('visitenkarten');
