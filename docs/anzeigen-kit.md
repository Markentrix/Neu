# ElbDetail Anzeigen-Kit: Google Ads und Meta Ads

Startphase lokal Celle. Stand: 16.10.2026 (Fakten von René ergänzt).

**Platzhalter:** Alles in `[PLATZHALTER: …]` muss der Betrieb entscheiden.

**Achtung Schreibweise:** In den Keyword-Tabellen sind `"…"` (Phrase Match) und `[…]` (Exact Match) die Google-Ads-Syntax. Das sind **keine** Platzhalter.

Texte, Tonalität und Fakten: siehe `docs/markenleitfaden.md`. Bilder und Videos: siehe `docs/foto-und-video-shotlist.md`.

---

## 1. Vor dem Start

- [ ] Alle Ziel-URLs sind live und laden fehlerfrei: `/termin.html`, `/gutscheine.html`, `/aktion/winterschutz.html`, `/firmenkunden.html`, `/preise.html`, `/elbdetail-care.html`, `/ueber-uns.html` und alle 7 Seiten unter `/leistungen/` (neu: `/leistungen/keramikversiegelung-celle.html`, `/leistungen/lederaufbereitung-celle.html`).
- [ ] Preisangaben in allen Texten als Endpreise ohne Umsatzsteuer-Hinweis (Kleinunternehmer nach § 19 UStG). Alle "ab"-Preise mit der Preisliste auf `/preise.html` abgleichen (vier Pakete Refresh, Essential, Signature, Excellence; niedrigster Ab-Preis gilt für Kleinwagen).
- [x] Inhalt der Winter-Aktion steht fest: Winterangebot mit Wachs = Innen- und Außenwäsche, Glanzpolitur und Wachsversiegelung; statt Wachs auf Wunsch C² CarCeramic (Aufpreis nach Absprache). Ab 329 € (Kleinwagen), 379 € (Kompakt), 449 € (Limousine/SUV), 549 € (Van/großer SUV), Sportwagen ab 599 € nach Besichtigung, gültig bis 28.02.2027. Anzeigentexte bei Bedarf daran anpassen.
- [x] Winter-Aktion Scheibenkeramik (21.10.2026 bis 28.02.2027): alle Außenscheiben 99 €, inklusive Panoramadach 114 €, inklusive Reinigung und üblicher Vorbereitung, auch einzeln buchbar, Dauer ca. 1 Stunde. Ziel-Link: `/termin.html?paket=scheiben`.
- [ ] Gutschein-Angebot steht fest: `[PLATZHALTER: Werte oder Pakete, Form (PDF, gedruckt), letzter Bestelltag vor Weihnachten]`.
- [ ] Test-Aufruf jeder Ziel-URL mit UTM-Parametern (Abschnitt 5). In der eigenen Statistik prüfen, dass Quelle und Kampagne ankommen.
- [ ] Test der Ereignisse: Termin angefragt, Gutschein angefragt, WhatsApp-Klick, Anruf-Klick werden in der Statistik gezählt.
- [ ] Google Business Profile mit identischer Adresse und Telefonnummer, verknüpft mit Google Ads (für Standort-Asset).
- [ ] Bewertungszahl in allen Texten aktuell (Stand Oktober 2026: 5,0 Sterne bei 22 Google-Rezensionen).
- [ ] Meta Business-Konto mit Facebook-Seite und Instagram-Konto verbunden.
- [ ] Zahlungsmittel in beiden Werbekonten hinterlegt, Rechnungsadresse korrekt.

---

## 2. Kampagnenstruktur und Budget

### 2.1 Struktur

| Kanal | Kampagne | Inhalt | Ziel-URL | Laufzeit |
|---|---|---|---|---|
| Google Suche | **G1 Leistungen Celle** | AG1 bis AG4 (allgemein, Innen, Lack, Leasing) und AG6 Keramikversiegelung | je Anzeigengruppe | Dauerhaft |
| Google Suche | **G2 Winterschutz Celle** | AG5 Winterschutz | `/aktion/winterschutz.html` | Ab sofort bis 28.02.2027 |
| Meta | **M1 Winterschutz** | Reels und Bilder Winter-Lackschutz | `/aktion/winterschutz.html` | Ab sofort bis 28.02.2027 |
| Meta | **M2 Weihnachtsgutscheine** | Gutscheine als Geschenk | `/gutscheine.html` | `[PLATZHALTER: Start, Empfehlung Mitte November]` bis `[PLATZHALTER: letzter Bestelltag]` |
| Meta | **M3 Innenraum/Hund** | Innenraum-Tiefenreinigung, Hundehaare, Gerüche | `/leistungen/innenaufbereitung-celle.html` | Dauerhaft, zuerst 4 Wochen Test |

**Warum so:**
- **Google Suche** erreicht Menschen, die schon suchen. Deshalb ist G1 die Basis und läuft dauerhaft.
- **Winterschutz als eigene Kampagne (G2)**, damit das saisonale Budget getrennt steuerbar ist und nach Aktionsende einfach pausiert wird.
- **Meta** erzeugt Nachfrage bei Menschen, die noch nicht suchen. Gut für Saison-Themen (Winter, Weihnachten) und für ein sichtbares Problem (Hundehaare), das man in Bildern zeigen kann.
- **Wenige Kampagnen** in der Startphase: Jede Kampagne braucht genug Budget, um Daten zu sammeln.

### 2.2 Budgetvorschlag

**Formel:** Monatsbudget = gewünschte Anfragen pro Monat × akzeptable Kosten pro Anfrage.

| Größe | Wert |
|---|---|
| Gewünschte Anfragen pro Monat (alle Kanäle) | `[PLATZHALTER: Anzahl]` |
| Akzeptable Kosten pro Anfrage | `[PLATZHALTER: € pro Anfrage, abgeleitet aus durchschnittlichem Auftragswert und Abschlussquote]` |
| **Monatsbudget gesamt** | `[PLATZHALTER: € pro Monat]` |

**Aufteilung als Empfehlung für Oktober bis Dezember:**

| Kampagne | Anteil | Monatsbudget | Tagesbudget (÷ 30,4) | Begründung |
|---|---|---|---|---|
| G1 Leistungen Celle | 45 % | `[PLATZHALTER: €]` | `[PLATZHALTER: €]` | Höchste Kaufabsicht, dauerhafte Basis. AG6 Keramik ist der strategische Schwerpunkt: in den ersten 4 Wochen beobachten und bei guter Anfragequote innerhalb von G1 bevorzugen |
| G2 Winterschutz Celle | 15 % | `[PLATZHALTER: €]` | `[PLATZHALTER: €]` | Saisonale Suche im Herbst |
| M1 Winterschutz | 15 % | `[PLATZHALTER: €]` | `[PLATZHALTER: €]` | Saison-Thema sichtbar machen, Reels mit Wasserperlen |
| M2 Weihnachtsgutscheine | 15 % | `[PLATZHALTER: €]` | `[PLATZHALTER: €]` | Nur Mitte November bis kurz vor Weihnachten, dann Budget zurück zu G1 |
| M3 Innenraum/Hund | 10 % | `[PLATZHALTER: €]` | `[PLATZHALTER: €]` | Test, ob das Thema auf Meta Anfragen bringt |

**Regeln:**
- Erst nach 4 Wochen Budget umschichten. Vorher sind die Zahlen zu klein.
- Umschichten nach Kosten pro Anfrage aus der eigenen Statistik (Abschnitt 5), nicht nach Klicks.
- Nach Aktionsende G2 und M1 pausieren und das Budget auf G1 legen.

### 2.3 Standort-Targeting

| Einstellung | Google Ads | Meta Ads |
|---|---|---|
| Mittelpunkt | Lachtehäuser Straße 1, 29223 Celle | Lachtehäuser Straße 1, 29223 Celle (Pin) |
| Radius | `[PLATZHALTER: km]` | `[PLATZHALTER: km]` |
| Option | "Präsenz": nur Personen, die sich im Gebiet befinden oder regelmäßig dort aufhalten. **Nicht** "Präsenz oder Interesse". | Personen, die dort wohnen oder sich kürzlich dort aufgehalten haben |
| Ausschluss | `[PLATZHALTER: Regionen ausschließen, z. B. Region Hannover, falls nicht gewünscht]` | wie Google |

**Empfehlung zum Radius:** Mit einem Radius starten, der die Stadt Celle mit allen Ortsteilen und die nahen Landkreis-Orte abdeckt (z. B. Wietze, Hambühren, Lachendorf, Wathlingen, Nienhagen, Adelheidsdorf, Eicklingen, Winsen (Aller)). Die nördlichen Orte (Bergen, Eschede, Hermannsburg, Faßberg, Unterlüß, Beedenbostel) im Kartenmodus prüfen und bei Bedarf als zusätzliche Orte hinzufügen, statt den Radius stark zu vergrößern. So bleibt das Budget im Einzugsgebiet.

### 2.4 Weitere Grundeinstellungen

| Einstellung | Google | Meta |
|---|---|---|
| Netzwerk | Nur Google-Suche. **Displaynetzwerk und Suchnetzwerk-Partner aus.** | Platzierungen: Instagram Feed, Reels, Stories; Facebook Feed, Reels |
| Sprache | Deutsch | Deutsch |
| Gebotsstrategie | "Klicks maximieren" mit Max-CPC-Limit `[PLATZHALTER: €]` oder manueller CPC. Gebotsstrategien auf Conversions sind ohne Conversion-Tracking im Werbekonto nicht sinnvoll (siehe Abschnitt 5.4). | Ziel "Traffic", Optimierung auf Link-Klicks. Landingpage-Aufrufe benötigen das Meta-Pixel und sind deshalb nicht verfügbar. |
| Werbezeitplan | `[PLATZHALTER: Zeiten, in denen Anfragen beantwortet werden]`. Anruf-Asset nur zu Erreichbarkeitszeiten. | Ganztägig |
| Alter | Keine Einschränkung | `[PLATZHALTER: Altersspanne, z. B. ab 18]` |
| Geräte | Alle, mobil im Blick behalten | Alle |

**Optional Meta:** Kampagne mit Ziel "Interaktion", Conversion-Ort WhatsApp (Klick-zu-WhatsApp-Anzeigen). Voraussetzung: Die Nummer +49 172 7613807 ist ein WhatsApp-Business-Konto und mit der Facebook-Seite verbunden `[PLATZHALTER: prüfen]`. Diese Klicks laufen nicht über die Website und erscheinen deshalb nicht in der eigenen Statistik. Gemessen wird dann über die Meta-Berichte (gestartete Unterhaltungen) und die eigene Strichliste (Abschnitt 5.3).

---

## 3. Google Ads

### 3.1 Anzeigengruppen

Pro Anzeigengruppe eine responsive Suchanzeige (RSA) mit 15 Headlines und 4 Descriptions. **H1 (Keyword-Headline) auf Position 1 fixieren**, alle anderen frei lassen. Zeichenlängen sind mit einem Skript geprüft (Headlines max. 30, Descriptions max. 90 Zeichen, Umlaute und Leerzeichen zählen je 1 Zeichen).

#### AG1 Fahrzeugaufbereitung allgemein

**Ziel-URL:** `/termin.html`  
**Hinweis:** Alternative zum Testen: /preise.html (Preise zuerst, dann Termin).  
**Keywords (23):** 18 Phrase Match, 5 Exact Match

| Phrase Match | Exact Match |
|---|---|
| `"fahrzeugaufbereitung celle"` | `[fahrzeugaufbereitung celle]` |
| `"autoaufbereitung celle"` | `[autoaufbereitung celle]` |
| `"auto aufbereitung celle"` | `[auto aufbereitung celle]` |
| `"fahrzeugaufbereiter celle"` | `[autopflege celle]` |
| `"autoaufbereiter celle"` | `[car detailing celle]` |
| `"fahrzeugpflege celle"` |  |
| `"autopflege celle"` |  |
| `"autoreinigung celle"` |  |
| `"auto reinigen lassen celle"` |  |
| `"auto handwäsche celle"` |  |
| `"car detailing celle"` |  |
| `"fahrzeugaufbereitung in der nähe"` |  |
| `"autoaufbereitung in der nähe"` |  |
| `"auto aufbereiten lassen"` |  |
| `"fahrzeugaufbereitung preise"` |  |
| `"autoaufbereitung kosten"` |  |
| `"fahrzeugaufbereitung landkreis celle"` |  |
| `"auto komplett reinigen lassen"` |  |

**Headlines (max. 30 Zeichen)**

| Nr. | Headline | Zeichen |
|---|---|---|
| H1 | Fahrzeugaufbereitung Celle | 26 |
| H2 | Autoaufbereitung in Celle | 25 |
| H3 | 100 % Handarbeit in Celle | 25 |
| H4 | Keine Waschstraße | 17 |
| H5 | 5,0 Sterne bei Google | 21 |
| H6 | Verbindlicher Preis vorab | 25 |
| H7 | Refresh ab 79 € | 15 |
| H8 | Essential ab 299 € | 18 |
| H9 | Termin per WhatsApp anfragen | 28 |
| H10 | Zwei-Eimer-Handwäsche | 21 |
| H11 | Mit Koch-Chemie-Produkten | 25 |
| H12 | Abnahme bei Tageslicht | 22 |
| H13 | Ihr Auto, wie neu. | 18 |
| H14 | Lachtehäuser Straße 1, Celle | 28 |
| H15 | Jetzt Termin anfragen | 21 |

**Descriptions (max. 90 Zeichen)**

| Nr. | Description | Zeichen |
|---|---|---|
| D1 | Fahrzeugaufbereitung in Celle: 100 % Handarbeit, keine Waschstraße. Jetzt Termin anfragen. | 90 |
| D2 | Verbindlicher Preis vor dem Termin, Abnahme bei Tageslicht. 5,0 Sterne bei Google. | 82 |
| D3 | Zwei-Eimer-Handwäsche mit Koch-Chemie-Produkten. Refresh ab 79 €. | 65 |
| D4 | Termin per WhatsApp oder online anfragen. Mo bis Fr, samstags nach Absprache. | 77 |

#### AG2 Innenreinigung

**Ziel-URL:** `/leistungen/innenaufbereitung-celle.html`  
**Keywords (21):** 17 Phrase Match, 4 Exact Match

| Phrase Match | Exact Match |
|---|---|
| `"innenreinigung auto celle"` | `[innenreinigung auto celle]` |
| `"auto innenreinigung celle"` | `[auto innenreinigung celle]` |
| `"autoinnenreinigung celle"` | `[innenaufbereitung celle]` |
| `"innenraumreinigung auto celle"` | `[autositze reinigen lassen]` |
| `"innenaufbereitung celle"` |  |
| `"auto innenraum reinigen lassen"` |  |
| `"auto innen reinigen lassen"` |  |
| `"polsterreinigung auto celle"` |  |
| `"autositze reinigen lassen"` |  |
| `"teppich auto reinigen lassen"` |  |
| `"hundehaare auto entfernen lassen"` |  |
| `"auto geruch entfernen lassen"` |  |
| `"geruchsentfernung auto"` |  |
| `"lederpflege auto celle"` |  |
| `"innenreinigung auto kosten"` |  |
| `"innenreinigung auto in der nähe"` |  |
| `"auto innenraum aufbereitung"` |  |

**Headlines (max. 30 Zeichen)**

| Nr. | Headline | Zeichen |
|---|---|---|
| H1 | Innenreinigung in Celle | 23 |
| H2 | Innenraum-Tiefenreinigung | 25 |
| H3 | Polster & Teppich reinigen | 26 |
| H4 | Geruchsneutralisation | 21 |
| H5 | Leder- oder Polsterpflege | 25 |
| H6 | Essential ab 299 € | 18 |
| H7 | Inkl. Kunststoffpflege | 22 |
| H8 | Auto voller Hundehaare? | 23 |
| H9 | Innenraum wieder frisch | 23 |
| H10 | Autoinnenreinigung Celle | 24 |
| H11 | 100 % Handarbeit | 16 |
| H12 | 5,0 Sterne bei Google | 21 |
| H13 | Verbindlicher Preis vorab | 25 |
| H14 | Termin per WhatsApp anfragen | 28 |
| H15 | Mit Koch-Chemie-Produkten | 25 |

**Descriptions (max. 90 Zeichen)**

| Nr. | Description | Zeichen |
|---|---|---|
| D1 | Innenraum-Tiefenreinigung in Celle: Polster, Teppich, Kunststoff, Geruchsneutralisation. | 88 |
| D2 | Essential ab 299 € inkl. Leder- oder Polsterpflege. Verbindlicher Preis vorab. | 78 |
| D3 | Hundehaare, Krümel, Gerüche? Innenraum gründlich von Hand gereinigt. Jetzt anfragen. | 84 |
| D4 | 5,0 Sterne bei 22 Google-Rezensionen. Termin per WhatsApp oder online anfragen. | 79 |

#### AG3 Lackpolitur und Versiegelung

**Ziel-URL:** `/leistungen/lackpolitur-celle.html`  
**Hinweis:** Keywords mit „versiegelung“ auf Keyword-Ebene mit der finalen URL /leistungen/lackversiegelung-celle.html hinterlegen. Keywords mit „keramik“ oder „coating“ gehören nicht in AG3, sondern in AG6 Keramikversiegelung.  
**Keywords (22):** 18 Phrase Match, 4 Exact Match

| Phrase Match | Exact Match |
|---|---|
| `"lackpolitur celle"` | `[lackpolitur celle]` |
| `"auto polieren lassen celle"` | `[auto polieren lassen celle]` |
| `"auto polieren celle"` | `[lackversiegelung celle]` |
| `"lackaufbereitung celle"` | `[auto versiegeln lassen celle]` |
| `"politur auto celle"` |  |
| `"kratzer auspolieren lassen"` |  |
| `"kratzer im lack entfernen lassen"` |  |
| `"hologramme entfernen auto"` |  |
| `"swirls entfernen lassen"` |  |
| `"auto polieren lassen kosten"` |  |
| `"lackversiegelung celle"` |  |
| `"auto versiegeln lassen celle"` |  |
| `"lackversiegelung auto"` |  |
| `"auto versiegeln lassen"` |  |
| `"felgenversiegelung"` |  |
| `"lackpolitur in der nähe"` |  |
| `"auto polieren lassen in der nähe"` |  |
| `"lack aufbereiten lassen"` |  |

**Headlines (max. 30 Zeichen)**

| Nr. | Headline | Zeichen |
|---|---|---|
| H1 | Lackpolitur in Celle | 20 |
| H2 | Lackversiegelung in Celle | 25 |
| H3 | Kratzer & Hologramme mindern | 28 |
| H4 | Mehrstufige Lackpolitur | 23 |
| H5 | Lackschichtdickenmessung | 24 |
| H6 | Messung vor jeder Politur | 25 |
| H7 | Excellence ab 599 € | 19 |
| H8 | Signature ab 449 € | 18 |
| H9 | Tiefer Glanz von Hand | 21 |
| H10 | 100 % Handarbeit | 16 |
| H11 | 5,0 Sterne bei Google | 21 |
| H12 | Verbindlicher Preis vorab | 25 |
| H13 | Koch-Chemie geschult | 20 |
| H14 | Abnahme bei Tageslicht | 22 |
| H15 | Jetzt Politur anfragen | 22 |

**Descriptions (max. 90 Zeichen)**

| Nr. | Description | Zeichen |
|---|---|---|
| D1 | Mehrstufige Lackkorrektur in Celle: reduziert korrigierbare Kratzer und Hologramme. | 83 |
| D2 | Lackschichtdickenmessung vor jeder Politur. Lackversiegelung separat buchbar. | 77 |
| D3 | Excellence ab 599 €. Verbindlicher Preis vor dem Termin, Abnahme bei Tageslicht. | 80 |
| D4 | Koch-Chemie geschult, C²Coating Excellence Partner. Jetzt Politur-Termin anfragen. | 82 |

#### AG4 Leasingrückgabe und Verkauf

**Ziel-URL:** `/leistungen/leasingrueckgabe-gebrauchtwagen-celle.html`  
**Keywords (18):** 15 Phrase Match, 3 Exact Match

| Phrase Match | Exact Match |
|---|---|
| `"leasingrückgabe aufbereitung"` | `[leasingrückgabe aufbereitung]` |
| `"aufbereitung leasingrückgabe celle"` | `[aufbereitung leasingrückgabe celle]` |
| `"auto vor leasingrückgabe aufbereiten"` | `[gebrauchtwagen aufbereitung celle]` |
| `"leasingrückgabe auto vorbereiten"` |  |
| `"leasingfahrzeug aufbereiten lassen"` |  |
| `"leasing rückgabe auto reinigen"` |  |
| `"auto aufbereiten vor verkauf"` |  |
| `"auto für verkauf aufbereiten"` |  |
| `"gebrauchtwagen aufbereitung celle"` |  |
| `"gebrauchtwagenaufbereitung"` |  |
| `"auto verkaufsfertig machen"` |  |
| `"fahrzeug aufbereiten vor verkauf"` |  |
| `"leasingrückgabe kratzer polieren"` |  |
| `"firmenwagen rückgabe aufbereitung"` |  |
| `"dienstwagen rückgabe aufbereitung"` |  |

**Headlines (max. 30 Zeichen)**

| Nr. | Headline | Zeichen |
|---|---|---|
| H1 | Vor der Leasingrückgabe | 23 |
| H2 | Leasingrückgabe in Celle | 24 |
| H3 | Auto für Verkauf aufbereiten | 28 |
| H4 | Gebrauchtwagen aufbereiten | 26 |
| H5 | Fahrzeug fit für die Rückgabe | 29 |
| H6 | Innen & außen von Hand | 22 |
| H7 | Lackkorrektur von Hand | 22 |
| H8 | Lackschichtdickenmessung | 24 |
| H9 | Verbindlicher Preis vorab | 25 |
| H10 | 5,0 Sterne bei Google | 21 |
| H11 | Abnahme bei Tageslicht | 22 |
| H12 | Gepflegt in die Übergabe | 24 |
| H13 | Essential ab 299 € | 18 |
| H14 | Termin per WhatsApp anfragen | 28 |
| H15 | 100 % Handarbeit | 16 |

**Descriptions (max. 90 Zeichen)**

| Nr. | Description | Zeichen |
|---|---|---|
| D1 | Aufbereitung vor Leasingrückgabe oder Verkauf in Celle. Innen und außen von Hand. | 81 |
| D2 | Lackschichtdickenmessung vor der Politur. Verbindlicher Preis vor dem Termin. | 77 |
| D3 | Gemeinsame Abnahme bei Tageslicht, damit Sie den Zustand vor der Übergabe kennen. | 81 |
| D4 | 100 % Handarbeit mit Koch-Chemie-Produkten. Termin per WhatsApp oder online anfragen. | 85 |

#### AG5 Winterschutz

**Ziel-URL:** `/aktion/winterschutz.html`  
**Hinweis:** Eigene Kampagne mit eigenem Budget, läuft nur bis [PLATZHALTER: Aktionsende]. Texte an den Aktionsinhalt der Seite anpassen.  
**Keywords (18):** 15 Phrase Match, 3 Exact Match

| Phrase Match | Exact Match |
|---|---|
| `"winterschutz auto"` | `[auto winterfest machen lassen]` |
| `"auto winterfest machen"` | `[winterschutz auto celle]` |
| `"auto winterfest machen lassen"` | `[lackversiegelung vor dem winter]` |
| `"lackschutz winter"` |  |
| `"auto lack winter schützen"` |  |
| `"lackversiegelung vor dem winter"` |  |
| `"auto versiegeln vor winter"` |  |
| `"auto winterfest celle"` |  |
| `"winterpflege auto"` |  |
| `"auto pflege winter"` |  |
| `"felgen versiegeln winter"` |  |
| `"streusalz lack schutz"` |  |
| `"auto aufbereitung herbst"` |  |
| `"winterschutz auto celle"` |  |
| `"lack versiegeln lassen winter"` |  |

**Headlines (max. 30 Zeichen)**

| Nr. | Headline | Zeichen |
|---|---|---|
| H1 | Winter-Lackschutz in Celle | 26 |
| H2 | Lack winterfest machen | 22 |
| H3 | Versiegelung vor dem Winter | 27 |
| H4 | Winter-Lackschutz-Aktion | 24 |
| H5 | Glanzpolitur vor dem Winter | 27 |
| H6 | Jetzt vor dem Winter buchen | 27 |
| H7 | Lackversiegelung in Celle | 25 |
| H8 | 100 % Handarbeit | 16 |
| H9 | Mit Koch-Chemie-Produkten | 25 |
| H10 | 5,0 Sterne bei Google | 21 |
| H11 | Verbindlicher Preis vorab | 25 |
| H12 | Lackschichtdickenmessung | 24 |
| H13 | Abnahme bei Tageslicht | 22 |
| H14 | Winterschutz per WhatsApp | 25 |
| H15 | Samstags nach Absprache | 23 |

**Descriptions (max. 90 Zeichen)**

| Nr. | Description | Zeichen |
|---|---|---|
| D1 | Winter-Lackschutz in Celle: Lack vor dem Winter polieren und versiegeln lassen. | 79 |
| D2 | Handwäsche, Lackversiegelung und Abnahme bei Tageslicht. Verbindlicher Preis vorab. | 83 |
| D3 | 100 % Handarbeit mit Koch-Chemie-Produkten. 5,0 Sterne bei Google. | 66 |
| D4 | Jetzt Termin vor dem ersten Frost anfragen. Per WhatsApp oder online. | 69 |

#### AG6 Keramikversiegelung (Schwerpunkt)

**Ziel-URL:** `/leistungen/keramikversiegelung-celle.html`  
**Kampagne:** G1 Leistungen Celle, `utm_content=ag-keramik`.  
**Hinweis:** Keine Preise in Headlines oder Descriptions. Die Richtpreise (C² CarCeramic, Pkw ab 550 € je nach C²Coating-Kategorie) stehen auf der Zielseite. Den verbindlichen Preis nennt René nach Lackprüfung, Besichtigung oder Fotos. 12 Headlines zum Start, bei Bedarf bis 15 ergänzen. `[PRÜFEN: Akzeptiert Google Ads das Zeichen "²" in "C²Coating"? Falls die Anzeige wegen Sonderzeichen abgelehnt wird, die Headline H3 durch "Offizieller Coating-Partner" (27) ersetzen und "C²Coating" nur auf der Zielseite nennen.]`  
**Keywords (20):** 16 Phrase Match, 4 Exact Match

| Phrase Match | Exact Match |
|---|---|
| `"keramikversiegelung celle"` | `[keramikversiegelung celle]` |
| `"keramikversiegelung auto celle"` | `[keramikversiegelung auto celle]` |
| `"keramik versiegelung celle"` | `[ceramic coating celle]` |
| `"ceramic coating celle"` | `[lackkorrektur celle]` |
| `"keramikbeschichtung auto celle"` |  |
| `"keramikversiegelung auto"` |  |
| `"keramikversiegelung lack"` |  |
| `"keramikversiegelung kosten"` |  |
| `"keramikversiegelung in der nähe"` |  |
| `"auto keramik versiegeln lassen"` |  |
| `"keramikversiegelung felgen"` |  |
| `"keramikversiegelung scheiben"` |  |
| `"lackkorrektur celle"` |  |
| `"lackkorrektur und keramikversiegelung"` |  |
| `"c2coating"` |  |
| `"coating auto celle"` |  |

**Headlines (max. 30 Zeichen)**

| Nr. | Headline | Zeichen |
|---|---|---|
| H1 | Keramikversiegelung Celle | 25 |
| H2 | Keramikversiegelung vom Profi | 29 |
| H3 | C²Coating Excellence Partner | 28 |
| H4 | Lackkorrektur vor Versiegelung | 30 |
| H5 | Keramik für Lack, Glas, Felgen | 30 |
| H6 | Glanz und Abperleffekt | 22 |
| H7 | Gründliche Lackvorbereitung | 27 |
| H8 | Pflege nach der Versiegelung | 28 |
| H9 | Persönliche Beratung in Celle | 29 |
| H10 | 100 % Handarbeit | 16 |
| H11 | 5,0 Sterne bei Google | 21 |
| H12 | Keramik-Termin anfragen | 23 |

**Descriptions (max. 90 Zeichen)**

| Nr. | Description | Zeichen |
|---|---|---|
| D1 | Keramikversiegelung in Celle für Lack, Glas und Felgen. Mit gründlicher Lackvorbereitung. | 89 |
| D2 | Als C²Coating Excellence Partner versiegeln wir Ihren Lack nach professioneller Korrektur. | 90 |
| D3 | Vor dem Coating: Handwäsche, Dekontamination, Lackkorrektur. Verbindlicher Preis vorab. | 87 |
| D4 | Termin per WhatsApp oder online anfragen. Wir beraten Sie gern zur passenden Versiegelung. | 90 |

### 3.2 Negative Keywords

Als **auszuschließende Keyword-Liste** "ElbDetail Negativ" anlegen und G1 und G2 zuweisen. Standard: weitgehend passend (Broad), d. h. ausgeschlossen werden Suchanfragen, die alle Wörter des Eintrags enthalten.

**73 Einträge:**

| Thema | Negative Keywords |
|---|---|
| Waschanlagen und Selbstbedienung | `waschstraße`, `waschanlage`, `portalwaschanlage`, `sb waschanlage`, `selbstwaschbox`, `waschbox`, `münzwaschanlage`, `tankstelle` |
| Jobs und Ausbildung | `job`, `jobs`, `stellenangebot`, `stellenangebote`, `ausbildung`, `minijob`, `gehalt`, `franchise` |
| Kurse und Selbermachen | `kurs`, `lehrgang`, `schulung`, `selber machen`, `selbst machen`, `anleitung`, `tutorial`, `diy`, `hausmittel` |
| Produkte und Geräte | `shop`, `amazon`, `ebay`, `kleinanzeigen`, `baumarkt`, `poliermaschine`, `polierpad`, `poliermittel`, `autoshampoo`, `mikrofasertuch`, `nassauger`, `dampfreiniger`, `hochdruckreiniger`, `kärcher` |
| Mieten und kostenlos | `mieten`, `leihen`, `kostenlos`, `gratis` |
| Information statt Auftrag | `wikipedia`, `definition`, `bedeutung`, `was ist`, `testsieger` |
| Haus und Wohnung | `wohnung`, `sofa`, `couch`, `matratze`, `fenster`, `gebäudereinigung` |
| Andere Gewerke | `lackierer`, `lackiererei`, `delle`, `dellen`, `beule`, `unfallschaden`, `steinschlag`, `smart repair`, `folierung`, `scheibentönung`, `reifenwechsel`, `winterreifen`, `ölwechsel`, `tüv` |
| Andere Städte | `hannover`, `hamburg`, `braunschweig`, `wolfsburg`, `bremen` |

**Vor dem Ausschließen entscheiden** (abhängig vom Angebot):

| Thema | Negative Keywords |
|---|---|
| Angebote, die nicht fest im Programm sind | `nano`, `mobil`, `mobile aufbereitung`, `vor ort`, `flatrate` |
| Fahrzeugarten | `wohnmobil`, `wohnwagen`, `motorrad`, `boot`, `lkw`, `oldtimer` |
| Preissuchende | `billig`, `günstig` |
| Nahe Städte außerhalb des Einzugsgebiets | `burgdorf`, `gifhorn`, `uelzen`, `soltau`, `peine` |

**Nicht mehr ausschließen:** `keramik`, `keramikversiegelung`, `ceramic` (Schwerpunkt, AG6), `abholservice`, `hol und bring` (Abhol- und Bringservice nach Vereinbarung). `abo` nicht pauschal ausschließen: Suchen wie "auto pflege abo" können zu ElbDetail Care passen. Im Bericht "Suchbegriffe" beobachten.

**Pflege:** Wöchentlich den Bericht "Suchbegriffe" prüfen. Unpassende Begriffe ergänzen.

### 3.3 Assets (Erweiterungen)

Auf Kontoebene anlegen, damit sie für G1 und G2 gelten. Asset "Winter-Lackschutz" nur bis Aktionsende, Asset "Gutscheine" bevorzugt ab November.

**Sitelinks (Text max. 25, Beschreibung je max. 35 Zeichen, Zeichenzahl in Klammern)**

| Sitelink-Text (max. 25) | Zeichen | Ziel-URL | Beschreibung 1 (max. 35) | Beschreibung 2 (max. 35) |
|---|---|---|---|---|
| Pakete & Preise | 15 | `/preise.html` | Vier Pakete, Richtpreise ab 79 € (32) | Verbindlicher Preis vorab (25) |
| Termin anfragen | 15 | `/termin.html` | Online oder per WhatsApp (24) | Mo bis Fr, Sa nach Absprache (28) |
| Innenaufbereitung | 17 | `/leistungen/innenaufbereitung-celle.html` | Tiefenreinigung, Polster, Teppich (33) | Geruchsneutralisation inklusive (31) |
| Lackpolitur | 11 | `/leistungen/lackpolitur-celle.html` | Mehrstufig, mit Messung vorab (29) | Mindert Kratzer und Hologramme (30) |
| Keramikversiegelung | 19 | `/leistungen/keramikversiegelung-celle.html` | Für Lack, Glas und Felgen (25) | C²Coating Excellence Partner (28) |
| Lackversiegelung | 16 | `/leistungen/lackversiegelung-celle.html` | Schutz vor Salz und UV (22) | Mit Koch-Chemie-Produkten (25) |
| Lederaufbereitung | 17 | `/leistungen/lederaufbereitung-celle.html` | Reinigen, pflegen, reparieren (29) | Lederreparatur mit Colourlock (29) |
| Leasingrückgabe | 15 | `/leistungen/leasingrueckgabe-gebrauchtwagen-celle.html` | Aufbereitung vor Rückgabe (25) | Auch vor dem Verkauf (20) |
| Winter-Lackschutz | 17 | `/aktion/winterschutz.html` | Lack winterfest machen (22) | Versiegelung vor dem Winter (27) |
| Gutscheine | 10 | `/gutscheine.html` | Fahrzeugpflege verschenken (26) | Ideal zu Weihnachten (20) |
| Firmenkunden & Flotten | 22 | `/firmenkunden.html` | Autohäuser, Fahrschulen, Flotten (32) | Konditionen auf Anfrage (23) |
| ElbDetail Care | 14 | `/elbdetail-care.html` | Regelmäßige Pflege nach Plan (28) | Individuell, nur auf Anfrage (28) |
| Über uns | 8 | `/ueber-uns.html` | René, Gründer von ElbDetail (27) | Koch-Chemie-Fachschulungen (26) |

**Callouts (max. 25 Zeichen)**

| Callout | Zeichen |
|---|---|
| 100 % Handarbeit | 16 |
| Keine Waschstraße | 17 |
| Zwei-Eimer-Handwäsche | 21 |
| Keramikversiegelung | 19 |
| Colourlock Lederreparatur | 25 |
| Lackschichtdickenmessung | 24 |
| Verbindlicher Preis vorab | 25 |
| Abnahme bei Tageslicht | 22 |
| Bar, Karte oder PayPal | 22 |
| Samstags nach Absprache | 23 |
| 5,0 Sterne bei Google | 21 |
| Koch-Chemie geschult | 20 |
| Termin per WhatsApp | 19 |

**Snippets (Werte max. 25 Zeichen, mind. 3 Werte je Header)**

| Header | Werte |
|---|---|
| Leistungen (engl. Services) | Keramikversiegelung, Lackkorrektur, Lackversiegelung, Innenraumaufbereitung, Lederreparatur, Handwäsche, Geruchsneutralisierung, Motorraumreinigung, Cabrioverdeckreinigung, Verkaufsaufbereitung |
| Typen (engl. Types) | Refresh, Essential, Signature, Excellence |
| Stadtteile (engl. Neighborhoods) | Altstadt, Neuenhäusen, Blumlage, Westercelle, Altencelle, Garßen, Klein Hehlen, Groß Hehlen, Vorwerk, Wietzenbruch |

**Anruf-Asset:** +49 172 7613807, nur zu Erreichbarkeitszeiten `[PLATZHALTER: Zeiten]`.

**Standort-Asset:** über das verknüpfte Google Business Profile (Lachtehäuser Straße 1, 29223 Celle).

**Preis-Asset (optional):** Typ "Leistungen", Einheit "ab". Refresh ab 79 €, Essential ab 299 €, Signature ab 449 €, Excellence ab 599 €, jeweils mit Ziel-URL `/preise.html`. Preise gelten für Kleinwagen bei normalem Pflegezustand. Es sind Endpreise: ElbDetail ist Kleinunternehmer nach § 19 UStG und berechnet keine Umsatzsteuer. Mehrkosten bei starker Verschmutzung oder intensiver Tierhaarentfernung möglich. Keine Keramik-Preise in das Preis-Asset aufnehmen.

**Bild-Assets:** Motive aus der Shotlist (01, 14, 27/28, 33) in 1:1 und 1,91:1. Kennzeichen unkenntlich.

---

## 4. Meta Ads

Ansprache Sie. Kurze Sätze. Nur Fakten aus dem Markenleitfaden. Call-to-Action-Button "Mehr dazu", bei Klick-zu-WhatsApp "WhatsApp-Nachricht senden". Pro Anzeigengruppe 2 bis 3 Creatives testen.

### 4.1 M1 Winterschutz

**Ziel-URL:** `/aktion/winterschutz.html`

**Primärtexte**

1. Streusalz, Matsch und Frost setzen Ihrem Lack zu. Mit dem Winter-Lackschutz von ElbDetail in Celle machen Sie Ihr Auto winterfest. `[PLATZHALTER: Aktionsinhalt in einem Satz]`. Den verbindlichen Preis kennen Sie vor dem Termin. Jetzt anfragen.
2. Von Hand statt Waschstraße. Wir waschen nach der Zwei-Eimer-Methode und arbeiten mit Profi-Produkten von Koch-Chemie. So kommt Ihr Lack versiegelt durch den Winter. Termin per WhatsApp: +49 172 7613807.
3. 5,0 Sterne bei 22 Google-Rezensionen. Jetzt auch für Ihren Lack vor dem Winter: Winter-Lackschutz in Celle. Termine Mo bis Fr, samstags nach Absprache. Zum Schluss nehmen wir Ihr Auto gemeinsam bei Tageslicht ab.

**Headlines:** "Winter-Lackschutz in Celle" | "Lack winterfest machen" | "Versiegelt durch den Winter"

**Beschreibung (Link-Beschreibung):** "100 % Handarbeit. Verbindlicher Preis vorab."

**Creative-Briefing**

| Punkt | Vorgabe |
|---|---|
| Formate | Reel 9:16, 15 Sekunden. Einzelbild 4:5. Optional Karussell 4:5 mit Felge, Lack, Scheibe |
| Hook (0 bis 2 s) | Wasser trifft versiegelten Lack in Zeitlupe, Perlen springen ab |
| Ablauf | Wasserperlen Makro, Felge sauber, Scheibe mit Perlen, Fahrzeug-Totale, Endkarte |
| Text-Overlay | "Bereit für Salz und Matsch?" dann "Winter-Lackschutz in Celle" dann "Termin per WhatsApp" |
| Motive (Shotlist) | 06, 33, 35, 38, 01 |
| Endkarte | Logo, "Winter-Lackschutz", "+49 172 7613807", elbdetail.de |
| Nicht zeigen | Schneeketten, Reifenwechsel, Leistungen, die nicht zur Aktion gehören |

### 4.2 M2 Weihnachtsgutscheine

**Ziel-URL:** `/gutscheine.html`

**Primärtexte**

1. Noch kein Geschenk für jemanden, der sein Auto liebt? Verschenken Sie eine Fahrzeugaufbereitung in 100 % Handarbeit von ElbDetail aus Celle. `[PLATZHALTER: Gutscheinwerte oder Pakete]`. Gutschein jetzt anfragen.
2. Refresh, Essential, Signature oder Excellence: Ein Gutschein für ein gepflegtes Auto, innen wie außen. Paketgutscheine gelten für einen Kleinwagen. Eingelöst wird nach Terminvereinbarung, Mo bis Fr, samstags nach Absprache. `[PLATZHALTER: bestätigen, ob Gutscheine je Paket möglich sind]`
3. Last-Minute-Geschenk für Celle und Umgebung: ein Gutschein von ElbDetail. `[PLATZHALTER: Form des Gutscheins und letzter Bestelltag vor Weihnachten]`. 5,0 Sterne bei 22 Google-Rezensionen.

**Headlines:** "Gutschein für Fahrzeugpflege" | "Schenken Sie ein sauberes Auto" | "Weihnachtsgeschenk aus Celle"

**Beschreibung (Link-Beschreibung):** "Gutschein online anfragen."

**Creative-Briefing**

| Punkt | Vorgabe |
|---|---|
| Formate | Einzelbild 4:5 und 1:1, Reel 9:16 mit 10 bis 15 Sekunden, Story 9:16 |
| Hook (0 bis 2 s) | Schlüsselübergabe in Nahaufnahme oder Gutschein-Karte am glänzenden Auto |
| Ablauf | Gutschein (Gestaltung nach Markenleitfaden), Hände bei der Arbeit, Abnahme bei Tageslicht, Endkarte |
| Text-Overlay | "Geschenkidee fürs Auto" dann "Gutschein von ElbDetail" dann "Jetzt anfragen" |
| Motive (Shotlist) | 56, 01, 48, 54 |
| Gestaltung | Weiß/Platin mit Anthrazit, Blau als Akzent. Kein Rot-Grün-Weihnachtslook, höchstens dezente Saison-Details |
| Endkarte | Logo, "Gutscheine", elbdetail.de/gutscheine |

### 4.3 M3 Innenraum/Hund

**Ziel-URL:** `/leistungen/innenaufbereitung-celle.html`

**Primärtexte**

1. Hundehaare im Kofferraum, Pfotenabdrücke auf der Rückbank, Geruch im ganzen Auto? Mit dem Paket Essential reinigen wir Innenraum und Kofferraum intensiv von Hand: Polster und Teppich, Einstiege, Türverkleidungen und Kunststoffe. Ab 299 € für Kleinwagen. Bei vielen Tierhaaren oder Gerüchen nennen wir Ihnen den Mehraufwand vorab.
2. Ihr Hund liebt Autofahren. Ihrem Innenraum sieht man das an. Schicken Sie uns 3 Fotos per WhatsApp an +49 172 7613807 und Sie erhalten einen verbindlichen Preis, bevor wir anfangen.
3. Innenraum-Tiefenreinigung in Celle, 100 % Handarbeit mit Koch-Chemie-Produkten. Essential ab 299 € (Kleinwagen), ab 329 € (Kompaktwagen), ab 379 € (Limousine, Kombi, kleinerer SUV), ab 449 € (großer SUV, Van). 5,0 Sterne bei 22 Google-Rezensionen.

**Headlines:** "Hundehaare? Kennen wir." | "Innenraum wieder frisch" | "Essential ab 299 €"

**Beschreibung (Link-Beschreibung):** "Verbindlicher Preis vor dem Termin."

**Creative-Briefing**

| Punkt | Vorgabe |
|---|---|
| Formate | Reel 9:16, 15 bis 20 Sekunden. Karussell 4:5 mit Vorher/Nachher (Kofferraum, Rückbank, Fußraum) |
| Hook (0 bis 2 s) | Nahaufnahme Hundehaare im Kofferraum-Teppich |
| Ablauf | Saugen, Bürsten, saubere Bahn im Teppich, Kofferraum-Totale nachher, Endkarte |
| Text-Overlay | "Hund an Bord?" dann "Kofferraum wieder frei." dann "Essential ab 299 €" |
| Motive (Shotlist) | 18, 60, 23, 25, 17 |
| Hund im Bild | Nur mit Einwilligung des Halters. Kein Hund im Fahrzeug während der Reinigung zeigen |
| Endkarte | Logo, "3 Fotos per WhatsApp, verbindlicher Preis", "+49 172 7613807" |
| Nicht zeigen | Keine Versprechen wie "100 % haarfrei" oder "garantiert geruchsfrei" |

---

## 5. Conversion-Messung

### 5.1 So wird gemessen

Die Website meldet Seitenaufrufe und Ereignisse **cookielos an die Statistik des Markentrix-Portals** (`/api/e`). Gezählt werden:

| Ereignis | Bedeutung | Hinweis |
|---|---|---|
| **Termin angefragt** | Online-Terminformular abgeschickt | Hauptziel |
| **Gutschein angefragt** | Gutschein-Anfrage abgeschickt | Hauptziel M2 |
| **WhatsApp-Klick** | Klick auf einen WhatsApp-Button | Klick, nicht gesendete Nachricht |
| **Anruf-Klick** | Klick auf die Telefonnummer | Klick, nicht geführtes Gespräch |

Die Statistik liest die **UTM-Parameter** aus der URL. Deshalb bekommt jede Anzeige UTM-Parameter. So ist jede Anfrage einer Quelle und Kampagne zuzuordnen.

### 5.2 UTM-Schema

**Regeln:** nur Kleinbuchstaben, keine Leerzeichen, keine Umlaute. Unterstrich zwischen den Teilen, Bindestrich innerhalb eines Teils.

| Parameter | Werte | Bedeutung |
|---|---|---|
| `utm_source` | `google` / `meta` | Werbeplattform |
| `utm_medium` | `cpc` (Google Suche) / `paid_social` (Meta) | Art der Anzeige |
| `utm_campaign` | `<jahr>_<kanal>_<thema>` | Kampagne, siehe Tabelle |
| `utm_content` (optional) | Anzeigengruppe oder Creative, z. B. `ag-innen`, `reel-hund-v1` | Feinere Auswertung `[PLATZHALTER: prüfen, ob die Statistik utm_content auswertet]` |

**Kampagnen-Werte:**

| Kampagne | utm_source | utm_medium | utm_campaign |
|---|---|---|---|
| G1 Leistungen Celle | `google` | `cpc` | `2026_search_leistungen` |
| G2 Winterschutz Celle | `google` | `cpc` | `2026_search_winterschutz` |
| M1 Winterschutz | `meta` | `paid_social` | `2026_meta_winterschutz` |
| M2 Weihnachtsgutscheine | `meta` | `paid_social` | `2026_meta_gutscheine` |
| M3 Innenraum/Hund | `meta` | `paid_social` | `2026_meta_innenraum-hund` |
| Optional Klick-zu-WhatsApp | (keine Website-URL, Messung in Meta) | | |

**Utm_content für Google (G1):** `ag-allgemein`, `ag-innen`, `ag-lack`, `ag-leasing`, `ag-keramik`. Für G2: `ag-winter`.

**Beispiel-URLs:**

```
https://www.elbdetail.de/leistungen/innenaufbereitung-celle.html?utm_source=google&utm_medium=cpc&utm_campaign=2026_search_leistungen&utm_content=ag-innen
https://www.elbdetail.de/aktion/winterschutz.html?utm_source=meta&utm_medium=paid_social&utm_campaign=2026_meta_winterschutz&utm_content=reel-wasserperlen-v1
https://www.elbdetail.de/gutscheine.html?utm_source=meta&utm_medium=paid_social&utm_campaign=2026_meta_gutscheine&utm_content=bild-schluessel-v1
```

**Einrichtung Google Ads:** Kampagne → Einstellungen → Optionen für Kampagnen-URL → **Suffix der finalen URL**:

```
utm_source=google&utm_medium=cpc&utm_campaign=2026_search_leistungen
```

Für G2 entsprechend `2026_search_winterschutz`. `utm_content` je Anzeigengruppe im Suffix der Anzeigengruppe ergänzen (dann dort den vollständigen Suffix eintragen, er ersetzt den Kampagnen-Suffix). Sitelinks übernehmen den Suffix automatisch.

**Einrichtung Meta:** Anzeige → Tracking → **URL-Parameter**:

```
utm_source=meta&utm_medium=paid_social&utm_campaign=2026_meta_winterschutz&utm_content=reel-wasserperlen-v1
```

Für jede Anzeige `utm_content` passend zum Creative setzen.

### 5.3 Auswertung

Monatlich, pro Kampagne:

1. **Kosten** aus Google Ads bzw. Meta-Werbeanzeigenmanager.
2. **Ereignisse** aus der eigenen Statistik, gefiltert nach `utm_campaign`.
3. **Kosten pro Anfrage** = Kosten ÷ (Termin angefragt + Gutschein angefragt + WhatsApp-Klick + Anruf-Klick). Zusätzlich getrennt ausweisen: Kosten pro "Termin angefragt".
4. **Abschluss** aus der eigenen Auftragsliste: Spalte "Quelle" bei jeder Anfrage pflegen (Google, Meta, Empfehlung, Google Maps, sonstiges). Bei WhatsApp und Telefon nachfragen: "Wie sind Sie auf uns aufmerksam geworden?"
5. **Umsatz aus Anzeigen** aus der Auftragsliste summieren.

WhatsApp-Klicks und Anruf-Klicks sind Absichten, keine sicheren Anfragen. Deshalb die echte Zahl der WhatsApp-Chats und Anrufe aus Anzeigen zusätzlich per Strichliste erfassen.

### 5.4 Werbepixel

**Google Analytics** steuert das Markentrix-Portal (Einwilligung über das Cookie-Fenster des Portals, „Analytics: an“ in den Kundeneinstellungen). Google-Ads-Tag und Meta-Pixel sind bewusst nicht eingebaut; Conversions lassen sich über die Verknüpfung von Google Ads mit GA4 auswerten.

Folgen für die Kampagnen:
- Die Werbeplattformen sehen keine Website-Conversions. Automatische Gebotsstrategien auf Conversions sind deshalb nicht sinnvoll. Gesteuert wird über Klicks, CPC-Limit und die eigene Auswertung.
- Anrufe direkt aus der Google-Anzeige (Anruf-Asset) kann Google selbst als Conversion zählen, ohne Code auf der Website, sofern im Konto verfügbar `[PLATZHALTER: prüfen und ggf. einrichten]`.

**Wenn später Pixel gewünscht sind:** nur mit Einwilligungsbanner nachrüsten (Opt-in vor dem Laden, Ablehnen gleichwertig zu Zustimmen). Datenschutzerklärung anpassen, Auftragsverarbeitung bzw. Datenübermittlung prüfen lassen. `[PLATZHALTER: Entscheidung Pixel ja/nein]`

---

## 6. Monats-KPIs

| KPI | Quelle | Zielwert Monat 1 | Zielwert ab Monat 3 |
|---|---|---|---|
| Impressionen | Google Ads, Meta | `[PLATZHALTER]` | `[PLATZHALTER]` |
| Klicks | Google Ads, Meta | `[PLATZHALTER]` | `[PLATZHALTER]` |
| Klickrate (CTR) Google Suche | Google Ads | `[PLATZHALTER: %]` | `[PLATZHALTER: %]` |
| Klickrate (CTR) Meta (Link) | Meta | `[PLATZHALTER: %]` | `[PLATZHALTER: %]` |
| Kosten pro Klick (CPC) | Google Ads, Meta | `[PLATZHALTER: €]` | `[PLATZHALTER: €]` |
| Kosten gesamt | Google Ads, Meta | `[PLATZHALTER: €]` | `[PLATZHALTER: €]` |
| Termin angefragt | Eigene Statistik | `[PLATZHALTER: Anzahl]` | `[PLATZHALTER: Anzahl]` |
| Gutschein angefragt (Nov/Dez) | Eigene Statistik | `[PLATZHALTER: Anzahl]` | `[PLATZHALTER: Anzahl]` |
| WhatsApp-Klicks | Eigene Statistik | `[PLATZHALTER: Anzahl]` | `[PLATZHALTER: Anzahl]` |
| Anruf-Klicks | Eigene Statistik | `[PLATZHALTER: Anzahl]` | `[PLATZHALTER: Anzahl]` |
| Kosten pro Anfrage (alle Ereignisse) | Berechnung 5.3 | `[PLATZHALTER: €]` | `[PLATZHALTER: €]` |
| Kosten pro "Termin angefragt" | Berechnung 5.3 | `[PLATZHALTER: €]` | `[PLATZHALTER: €]` |
| Gebuchte Termine aus Anzeigen | Auftragsliste | `[PLATZHALTER: Anzahl]` | `[PLATZHALTER: Anzahl]` |
| Abschlussquote (Termine ÷ Anfragen) | Auftragsliste | `[PLATZHALTER: %]` | `[PLATZHALTER: %]` |
| Umsatz aus Anzeigen | Auftragsliste | `[PLATZHALTER: €]` | `[PLATZHALTER: €]` |
| Umsatz ÷ Werbekosten | Berechnung | `[PLATZHALTER]` | `[PLATZHALTER]` |
| Neue Google-Rezensionen | Google Business Profile | `[PLATZHALTER: Anzahl]` | `[PLATZHALTER: Anzahl]` |

### Wöchentliche Routine (15 Minuten)

1. Google: Suchbegriffe prüfen, Negative ergänzen.
2. Google und Meta: Kosten im Plan? Kampagnen mit Kosten, aber ohne Ereignisse markieren.
3. Meta: Häufigkeit über ca. 3 pro Woche? Dann neues Creative einsetzen.
4. Eigene Statistik: Ereignisse nach `utm_campaign` notieren.

### Monatliche Routine

1. KPI-Tabelle ausfüllen.
2. Budget nach Kosten pro Anfrage umschichten (frühestens nach 4 Wochen).
3. Schwächste Headline je Anzeigengruppe ersetzen (Bewertung "Niedrig" in Google Ads).
4. Bewertungszahl in allen Anzeigen aktualisieren.
