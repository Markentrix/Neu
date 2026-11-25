-- E-Rechnung: Käuferreferenz bzw. Leitweg-ID (BT-10), nur bei Rechnungen an Behörden Pflicht
ALTER TABLE belege ADD COLUMN IF NOT EXISTS kaeufer_referenz text NOT NULL DEFAULT '';
