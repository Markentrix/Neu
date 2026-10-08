# Bestell-Backend (vorbereitet, noch nicht angeschlossen)

Das Formular ist fertig. Solange `orderEndpoint` in `config.js` leer ist, zeigt die Seite den Bestelltext zum Kopieren bzw. zum Versand per E-Mail an. Sobald dort eine URL steht, sendet das Formular die Bestellung per `POST` (JSON) an diese URL.

## Vertrag

**Anfrage** `POST <orderEndpoint>`, `Content-Type: application/json`

```json
{
  "ref": "KW-261008-A7QZ",
  "type": "vorbestellung",            // oder "feier"
  "name": "Erika Muster",
  "phone": "05144 123456",
  "email": null,
  "date": "2026-10-15",              // Wunschtermin (ISO)
  "time": "10:00–13:00",             // oder null
  "guests": null,                     // nur bei "feier"
  "occasion": null,                   // nur bei "feier"
  "items": [{ "name": "Schnitzel", "qty": 1.5, "unit": "kg" }],
  "notes": null,
  "consent": true,
  "consentAt": "2026-10-08T08:00:00.000Z",
  "hp": "",                           // Honeypot, muss leer sein
  "fillSeconds": 42                   // Ausfüllzeit, sehr kleine Werte = Bot
}
```

**Antwort** `200 OK` (optional `{ "ref": "KW-…" }`, sonst gilt die Nummer aus der Anfrage). Jeder andere Status zeigt dem Kunden eine Fehlermeldung mit Telefon und Textfallback.

## Was das Backend prüfen sollte
- `hp` leer und `fillSeconds >= 3`, sonst verwerfen.
- Pflichtfelder, Längen, `consent === true`, Datum in der Zukunft und kein Ruhetag (Sa/So/Mo).
- Rate-Limit pro IP, CORS nur für die eigene Domain.
- Benachrichtigung an die Fleischerei (E-Mail oder Push) bei jeder neuen Bestellung.

## Beispiel mit Supabase (nur Vorlage, nicht eingerichtet)

```sql
create table orders (
  id uuid primary key default gen_random_uuid(),
  ref text unique not null,
  created_at timestamptz not null default now(),
  type text not null check (type in ('vorbestellung','feier')),
  name text not null,
  phone text not null,
  email text,
  pickup_date date not null,
  pickup_time text,
  guests int,
  occasion text,
  items jsonb not null default '[]',
  notes text,
  consent_at timestamptz not null,
  status text not null default 'neu' check (status in ('neu','bestätigt','erledigt','storniert'))
);
alter table orders enable row level security;  -- keine öffentliche Policy: nur die Edge Function schreibt (service role)
```

Edge Function `order` (Deno), Grundgerüst:

```ts
import { createClient } from "jsr:@supabase/supabase-js@2";
const cors = { "Access-Control-Allow-Origin": "https://www.example.de",
  "Access-Control-Allow-Headers": "content-type", "Access-Control-Allow-Methods": "POST, OPTIONS" };
Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: cors });
  const b = await req.json();
  if (b.hp || b.fillSeconds < 3 || !b.consent || !b.name || !b.phone || !b.date)
    return new Response("invalid", { status: 400, headers: cors });
  const db = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
  const { error } = await db.from("orders").insert({
    ref: b.ref, type: b.type, name: b.name, phone: b.phone, email: b.email,
    pickup_date: b.date, pickup_time: b.time, guests: b.guests, occasion: b.occasion,
    items: b.items, notes: b.notes, consent_at: b.consentAt });
  if (error) return new Response("error", { status: 500, headers: cors });
  // TODO: E-Mail an die Fleischerei senden
  return new Response(JSON.stringify({ ref: b.ref }), { headers: { ...cors, "Content-Type": "application/json" } });
});
```

## Datenschutz beim Anschluss
Sobald Bestellungen auf einen Server gehen, müssen Datenschutzerklärung (Abschnitt 4: Empfänger, Speicherdauer, Auftragsverarbeitung) und Hinweistext im Formular angepasst und ein Vertrag zur Auftragsverarbeitung mit dem Anbieter geschlossen werden. Server in der EU wählen.
