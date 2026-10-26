-- Push-Erinnerung vor vereinbarten Anrufen: Rückruf mit Uhrzeit am Lead, Merker je Erinnerung am Erstgespräch
ALTER TABLE leads ADD COLUMN IF NOT EXISTS rueckruf_am timestamptz;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS rueckruf_push smallint NOT NULL DEFAULT 0;   -- 1 = Erinnerung 1 Stunde vorher gesendet, 3 = auch 5 Minuten vorher
ALTER TABLE gespraechstermine ADD COLUMN IF NOT EXISTS push_60 boolean NOT NULL DEFAULT false;
ALTER TABLE gespraechstermine ADD COLUMN IF NOT EXISTS push_5 boolean NOT NULL DEFAULT false;
