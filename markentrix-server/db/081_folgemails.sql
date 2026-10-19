-- Automatische Folgemails an Leads (mit Einwilligung) und Feedback-Mail an Kunden; Abmeldung per Link
ALTER TABLE leads ADD COLUMN IF NOT EXISTS folge_stufe int NOT NULL DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS folge_gesendet_am timestamptz;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS abgemeldet boolean NOT NULL DEFAULT false;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS abmelde_token text UNIQUE;
ALTER TABLE kunden ADD COLUMN IF NOT EXISTS feedback_mail_am timestamptz;
