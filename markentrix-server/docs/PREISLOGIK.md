# Preis- und Paketlogik: Entwurf zur Entscheidung (Stand 23.10.2026)

**Zweck:** Eine feste Linie für das Angebotsgespräch und für Upgrades, damit Vertriebler nicht improvisieren. **Das ist ein Entwurf.** Nichts davon ist im Portal umgesetzt oder freigegeben. Preise, Provisionen und Vertragsfragen bleiben deine Entscheidung (Rechtliches: Anwalt, siehe `docs/ANWALT-CHECKLISTE.md`).

## 1. Ausgangslage
- **Preise (Preisliste Stand September 2026, von dir bestätigt):** KI ONE 349 € / Monat + 1.490 € Einrichtung, BUSINESS 699 € + 2.490 €, KOMPLETT 1.190 € + 3.490 €. Zahlung der Einrichtung: 50 % Anzahlung, 50 % bei Abnahme. Kombivorteil 500 € Nachlass.
- **Provision im System (Entwurf, noch nicht freigegeben):** 20 % Monat 1 bis 12, 10 % Monat 13 bis 24, ab Monat 25 nichts; 5 % Verlängerungsbonus; Nachlauf 6 Monate nach Kündigung. Aus dem Code abgeleitet: Die Basis ist der berechnete Monatsbetrag abzüglich Rabatt; Rückbuchungen gibt es.
- **Offen:** Die Provisionsregeln stehen im Portal noch auf „Entwurf“. Vertriebler sehen die Sätze erst nach Freigabe.

## 2. Die drei Kundenfragen und ein Vorschlag je Frage
| Frage | Vorschlag | Entscheidung nötig |
|---|---|---|
| **Was kostet mehr Leistung?** | Pakete bleiben die Grundlage. Zusatzmodule als feste Preisliste mit Monatspreis, im Angebot einzeln ausgewiesen. Keine Einzelpreise am Telefon. | Gelten die Zusatzmodul-Preise (bisher 29 bis 59 € / Monat) noch? |
| **Wie viele Mitarbeiter und Leistungen sind enthalten?** | Je Paket eine Grenze für Kalender-Mitarbeiter (z. B. ONE bis 2, BUSINESS bis 5, KOMPLETT unbegrenzt). Darüber hinaus Aufpreis je weitere Person. | Grenzen und Aufpreis festlegen. |
| **Wie lange läuft der Vertrag?** | Eine feste Mindestlaufzeit (Vorschlag 12 Monate), danach monatlich mit 3 Monaten Frist kündbar. Gleiche Regel für alle Pakete. | Laufzeit und Frist; juristische Formulierung durch den Anwalt. |

## 3. Upgrade, Downgrade und Provision (der wichtigste Punkt)
Vorschlag, damit Vertriebler fair bezahlt werden und du keine Schlupflöcher baust:
1. **Die Vertragsmonate laufen weiter** ab dem ersten Abschluss. Ein Upgrade startet keine neue 20-%-Phase.
2. **Der Mehrbetrag** nach einem Upgrade wird mit dem Satz des aktuellen Vertragsmonats provisioniert (Monat 1 bis 12: 20 %, 13 bis 24: 10 %).
3. **Die Einrichtungsgebühr** ist nach deiner Entscheidung provisionspflichtig oder nicht. Der Entwurf geht davon aus, dass **nur der monatliche Betrag** provisioniert wird (wie im System berechnet).
4. **Downgrade:** Die Provision sinkt ab dem Folgemonat mit dem neuen Betrag. Bereits ausgezahlte Beträge werden nicht zurückgefordert.
5. **Kündigung in den ersten 3 Monaten:** Rückbuchung der Provision (das System kennt Rückbuchungen). Danach Nachlauf wie vereinbart.
6. **Zusatzmodule** zählen zur Basis, solange sie im selben Vertrag laufen.
7. **Wechsel des Vertrieblers beim Kunden:** nur durch dich, mit Notiz im Protokoll.

## 4. Was im Gespräch gilt (kurz für den Vertrieb)
- Preise nennt der Vertriebler nur aus der Preisliste, nie als Verhandlung.
- Bei Wünschen außerhalb der Pakete: „Das stelle ich Ihnen im Angebot zusammen.“ Dann die Anfrage im Lead stellen.
- Rabatte (außer dem Kombivorteil) gibt nur Markentrix.

## 5. Entscheidungen, die ich von dir brauche
- [ ] Zusatzmodul-Preise bestätigen oder neu festlegen
- [ ] Mitarbeiter-Grenzen je Paket und Aufpreis
- [ ] Mindestlaufzeit und Kündigungsfrist
- [ ] Einrichtungsgebühr provisionspflichtig: ja / nein
- [ ] Rückbuchungsfrist bei früher Kündigung (Vorschlag 3 Monate)
- [ ] Provisionsregeln im Admin freigeben (Preise & Konditionen)
- [ ] Anwalt: Laufzeit, Kündigung und Provisionsvereinbarung prüfen lassen

Wenn du die Punkte entschieden hast, baue ich: die Mitarbeiter-Grenzen im Portal, die Paket-Übersicht im Angebot und die Prüfung beim Upgrade (mit Hinweis an den Admin statt automatischer Provisionsänderung).

## Hinweis: Pakete im Kundenportal dazubuchen
Kunden buchen Pakete im Portal als `angefragt`; erst die Bestätigung durch Admin macht sie `beauftragt`. Referenzkunden buchen zu 0 €. Provisionen folgen den Buchungen: Ob dazugebuchte Pakete (und die Einrichtungsgebühr) provisionspflichtig sind, ist weiter eine offene Entscheidung aus der Liste oben.
