-- 157 Frei anlegbare Katalog-Pakete: neue Kategorie "kombi" (z. B. Website + Google-Anzeige im Monat), Kennzeichen "eigen".
-- Preise bleiben versioniert in produkt_preise, Module in produkt_module. Die festen Pakete ändern sich nicht.
BEGIN;
ALTER TABLE produkte DROP CONSTRAINT IF EXISTS produkte_kategorie_check;
ALTER TABLE produkte ADD CONSTRAINT produkte_kategorie_check
  CHECK (kategorie IN ('ki','website','ci','sichtbarkeit','personal_branding','lead','kombi'));
ALTER TABLE produkte ADD COLUMN IF NOT EXISTS eigen boolean NOT NULL DEFAULT false;
COMMIT;
