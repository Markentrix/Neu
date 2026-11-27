-- 158 Staffelpreise je Monat (z. B. Monat 1: 149 €, Monat 2: 199 €, ab Monat 3: 249 €).
-- staffel = [{"ab_monat":1,"cent":14900},{"ab_monat":2,"cent":19900},{"ab_monat":3,"cent":24900}] oder NULL (fester Monatspreis).
-- monatlich_cent bleibt der Preis der letzten Stufe (Regelpreis). Eine Buchung friert die Staffel bei der Buchung ein.
BEGIN;
ALTER TABLE produkt_preise ADD COLUMN IF NOT EXISTS staffel jsonb;
ALTER TABLE buchungen ADD COLUMN IF NOT EXISTS staffel jsonb;

-- Preis im Vertragsmonat vm (1 = erster Monat); ohne Staffel gilt der Regelpreis.
CREATE OR REPLACE FUNCTION mk_monatspreis(staffel jsonb, regel bigint, vm int) RETURNS bigint LANGUAGE sql IMMUTABLE AS $$
  SELECT COALESCE((SELECT (e->>'cent')::bigint FROM jsonb_array_elements(staffel) e
                   WHERE (e->>'ab_monat')::int <= vm ORDER BY (e->>'ab_monat')::int DESC LIMIT 1), regel)
$$;

CREATE OR REPLACE VIEW v_preise_aktuell WITH (security_invoker = true) AS
SELECT DISTINCT ON (p.code) p.code, p.kategorie, p.name, p.abrechnung, p.laufzeit_monate,
       pp.einrichtung_cent, pp.monatlich_cent, pp.projekt_cent, pp.ab_preis, pp.gueltig_ab,
       p.inklusive_minuten, p.inklusive_nachrichten, p.mehrminutenpreis_cent, p.nur_auf_anfrage, pp.staffel
FROM produkte p
LEFT JOIN produkt_preise pp ON pp.produkt_code = p.code AND pp.gueltig_ab <= current_date
WHERE p.aktiv
ORDER BY p.code, pp.gueltig_ab DESC;
COMMIT;
