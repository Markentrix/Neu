-- Fehlermeldungen aus Workflows: Benachrichtigungsmarker (Tabelle entsteht in 070)
ALTER TABLE workflow_fehler ADD COLUMN IF NOT EXISTS benachrichtigt boolean;
UPDATE workflow_fehler SET benachrichtigt = true WHERE benachrichtigt IS NULL;
ALTER TABLE workflow_fehler ALTER COLUMN benachrichtigt SET DEFAULT false;
ALTER TABLE workflow_fehler ALTER COLUMN benachrichtigt SET NOT NULL;
