-- Gutscheine im Online-Shop einlösen: Ablaufdatum und eingelöster Betrag am Gutschein, Gutschein-Abzug an der Bestellung
ALTER TABLE website_gutscheine ADD COLUMN IF NOT EXISTS gueltig_bis date;
ALTER TABLE website_gutscheine ADD COLUMN IF NOT EXISTS eingeloest numeric(10,2) NOT NULL DEFAULT 0 CHECK (eingeloest >= 0);
ALTER TABLE shop_bestellungen ADD COLUMN IF NOT EXISTS gutschein_id uuid REFERENCES website_gutscheine(id) ON DELETE SET NULL;
ALTER TABLE shop_bestellungen ADD COLUMN IF NOT EXISTS gutschein_code text;
ALTER TABLE shop_bestellungen ADD COLUMN IF NOT EXISTS gutschein_cent integer NOT NULL DEFAULT 0 CHECK (gutschein_cent >= 0);
