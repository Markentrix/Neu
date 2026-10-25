-- Lead-Funnel, Teil 2: Vorlage „Website-Check“ mit Ampel, Ergebnis-Mail samt PDF und eigene Nachfass-Mails je Kampagne.
-- Alles ist ab Werk aus (check_mail, folge_aktiv). Bestehende Kampagnen behalten die Vorlage „standard“ und verhalten sich wie bisher.

ALTER TABLE lead_kampagnen ADD COLUMN IF NOT EXISTS vorlage text NOT NULL DEFAULT 'standard' CHECK (vorlage IN ('standard','website_check'));
ALTER TABLE lead_kampagnen ADD COLUMN IF NOT EXISTS kicker text NOT NULL DEFAULT '';
ALTER TABLE lead_kampagnen ADD COLUMN IF NOT EXISTS check_mail boolean NOT NULL DEFAULT false;
ALTER TABLE lead_kampagnen ADD COLUMN IF NOT EXISTS check_betreff text NOT NULL DEFAULT 'Ihr Website-Check für {website}: {score} von 100 Punkten';
ALTER TABLE lead_kampagnen ADD COLUMN IF NOT EXISTS check_text text NOT NULL DEFAULT
  E'Guten Tag {name},\n\nIhr Website-Check ist fertig, das PDF hängt an.\n\nKurz zusammengefasst: {zusammenfassung} Ihre Website erreicht {score} von 100 Punkten.\n{punkte}\n\nWir rufen Sie kurz an, um das Ergebnis zu erklären. Wenn Ihnen ein fester Termin lieber ist, wählen Sie hier 15 Minuten: {buchen}';
ALTER TABLE lead_kampagnen ADD COLUMN IF NOT EXISTS folge_aktiv boolean NOT NULL DEFAULT false;
ALTER TABLE lead_kampagnen ADD COLUMN IF NOT EXISTS folge_tage int[] NOT NULL DEFAULT '{1,3,7}';
ALTER TABLE lead_kampagnen ADD COLUMN IF NOT EXISTS folge_betreffe text[] NOT NULL DEFAULT ARRAY[
  'Der wichtigste Punkt aus Ihrem Website-Check',
  'So sieht ein Betrieb aus, den man sofort anruft',
  'Sollen wir Ihren Website-Check schließen?'];
ALTER TABLE lead_kampagnen ADD COLUMN IF NOT EXISTS folge_texte text[] NOT NULL DEFAULT ARRAY[
  E'Guten Tag {name},\n\nvon allen Punkten im Check bringt einer am meisten: {wichtigster_punkt}\n\nSollen wir Ihnen zeigen, wie das bei Ihnen aussehen könnte? 15 Minuten reichen: {buchen}',
  E'Guten Tag {name},\n\nviele Betriebs-Websites verschenken Anfragen: kein Anruf-Knopf oben auf dem Handy, keine Preise, kein Gesicht.\n\nEine erneuerte Website von uns hat das ab dem ersten Tag, und Sie bekommen vorher ein festes Angebot. Termin für ein kurzes Gespräch: {buchen}',
  E'Guten Tag {name},\n\nwir haben noch nichts von Ihnen gehört, das ist völlig in Ordnung. Wir schließen Ihren Website-Check in den nächsten Tagen.\n\nWenn das Thema später wieder aufkommt, antworten Sie einfach auf diese Mail.'];

ALTER TABLE lead_checks ADD COLUMN IF NOT EXISTS token text UNIQUE;
ALTER TABLE lead_checks ADD COLUMN IF NOT EXISTS status text NOT NULL DEFAULT 'fertig' CHECK (status IN ('laeuft','fertig','fehler'));
ALTER TABLE lead_checks ADD COLUMN IF NOT EXISTS ampel text CHECK (ampel IS NULL OR ampel IN ('gruen','gelb','rot'));
ALTER TABLE lead_checks ADD COLUMN IF NOT EXISTS kampagne_id uuid REFERENCES lead_kampagnen(id) ON DELETE SET NULL;
ALTER TABLE lead_checks ADD COLUMN IF NOT EXISTS versuche int NOT NULL DEFAULT 0;
ALTER TABLE lead_checks ADD COLUMN IF NOT EXISTS mail_gesendet_am timestamptz;
ALTER TABLE lead_checks ADD COLUMN IF NOT EXISTS mail_versuche int NOT NULL DEFAULT 0;
ALTER TABLE lead_checks ADD COLUMN IF NOT EXISTS mail_versucht_am timestamptz;
-- Seit wann der Lead zur Kampagne gehört (Nachfass-Tage zählen ab hier, nicht ab dem ersten Kontakt)
ALTER TABLE leads ADD COLUMN IF NOT EXISTS kampagne_seit timestamptz;
CREATE INDEX IF NOT EXISTS lead_checks_offen_idx ON lead_checks (erstellt_am) WHERE status = 'laeuft';

-- Welche Nachfass-Mail einer Kampagne ein Lead schon bekommen hat (je Stufe genau einmal)
CREATE TABLE IF NOT EXISTS lead_funnel_folge (
  lead_id uuid NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  stufe int NOT NULL CHECK (stufe BETWEEN 1 AND 5),
  gesendet_am timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (lead_id, stufe)
);
SELECT rls_intern('lead_funnel_folge');
