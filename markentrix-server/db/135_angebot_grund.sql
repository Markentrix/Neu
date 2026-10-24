-- Warum wurde ein Angebot nicht angenommen? Grund (Auswahl) und freier Text, vom Team oder vom Empfänger (Online-Ablehnung)
ALTER TABLE belege ADD COLUMN IF NOT EXISTS grund_code text;
ALTER TABLE belege ADD COLUMN IF NOT EXISTS grund_text text;
ALTER TABLE belege ADD COLUMN IF NOT EXISTS grund_am timestamptz;
