---
name: "markentrix-werbevideo"
description: "Erstellt CI-konforme, rechtssichere KI-UGC-Werbevideos (Meta/TikTok Lead-Ads, Reels, Shorts) für Markentrix ausschließlich über die Higgsfield-API (pay-as-you-go, Python-Modul higgsfield_api) – von Briefing und Skript bis QA, Endcard, Post-Paket und A/B-Varianten. Nie über den Higgsfield-Connector oder Plan-Credits."
---

# Markentrix Werbevideo – Produktionsskill (API-Version)

Verbindliche Markentrix-Schicht über der Higgsfield-API. Legt fest, WAS gesagt und gezeigt wird (Marke, Angebot, Ton, Recht) und WIE produziert und geprüft wird. Die technische Pipeline ist das Python-Modul `higgsfield_api` im Repo (Abschnitt 0). Die früheren Connector-Workflows (get_workflow_instructions, ugc-review-video, De-Slop, Sandbox) werden nicht mehr benutzt.

Quellen der Wahrheit (immer aus dem Projekt „Markentrix“ lesen): Markentrix_CI_2026_White_Light_Premium_MASTER.pdf, Markentrix_Preisliste_01.10.2026.pdf, claude/creative-system/ (ci-design-system.mjs, README.md), Logo-Dateien. Bei Widerspruch gilt die aktuelle Projektdatei.

## 0. Technik: nur API, nie Connector
- Jede Generierung läuft über `python -m higgsfield_api …` oder `from higgsfield_api import HiggsfieldClient`. Niemals Tools mit Präfix `mcp__Higgsfield__` aufrufen (generate_video, execute_preset, get_workflow_instructions, media_upload_widget, ai_influencer_*, jobs_wait, show_* usw.). Die verbrauchen Plan-Credits des Nutzerkontos, das gekündigt ist.
- Zugang: In der Claude-Cloud-Umgebung hängt der Proxy den API-Key an api.higgsfield.ai selbst an. Lokal `HF_KEY="ID:SECRET"`. Key nie in Chat, Dateien oder Repo. Vor jeder Serie `python -m higgsfield_api check` (kostenlos).
- Kosten: vor jedem kostenpflichtigen Aufruf `--dry-run` oder `estimate_cost()` zeigen; Listenpreis ist Obergrenze, verbindlich ist console.higgsfield.ai. Erst ein Testclip pro Serie/Branche, dann Varianten; keine Massengenerierung ohne Freigabe. Unbeaufsichtigt: nichts Kostenpflichtiges über den freigegebenen Rahmen hinaus starten.
- Medien: Lokale Bilder/Ton mit `client.upload()` hochladen (liefert öffentliche URL). Ergebnisse sofort nach `output/` laden, Higgsfield hält Dateien nur mindestens 7 Tage. Fehlgeschlagene/NSFW-Jobs kosten nichts.
- Modelle (Kurznamen in `higgsfield_api/models.py`):
  - Host-Bild: `soul2` (SOUL V2, 9:16, 1080p), Standardlook in `higgsfield_api/ugc.py` (HOST_LOOK).
  - Sprecher-Clip Standard: `seedance2-ref` (Seedance 2.0 reference-to-video, Host-Bild als `image_urls`, nativer Ton, 4–15 s, 9:16, 1080p). Alternativen: `kling3-std-i2v`/`kling3-pro-i2v` (günstiger, 3–15 s, sound on), `seedance25-ref` (bis 30 s, teurer). Gesperrte Modelle nie tauschen, ohne das im Report zu nennen.
  - Eigene Tonspur (z. B. extern erzeugte Stimme) nur bei Seedance über `audio_urls`; dann spricht das Modell lippensynchron zur Spur. Stimmen nie von realen Personen klonen.
  - B-Roll/Produkt ohne Sprache: `kling-std-i2v`, `hailuo-i2v`.
- Nachbearbeitung lokal mit ffmpeg über `higgsfield_api/post.py`: `qa_frames` (Standbilder), `make_srt`/`burn_subtitles` (Untertitel), `overlay_png` (Hook-Plate, KI-Icon), `append_endcard`, `concat`. Endcard/Karten/Hook-Plate kommen aus dem CI-Renderer (claude/creative-system, Playwright/Chromium), nie aus der Generierung.
- Aussprache prüfen: Tonspur mit ffmpeg nach WAV (16 kHz mono) und lokal per faster-whisper (Modell „base“, Sprache de) transkribieren; Abweichungen vom Skript sind ein QA-Mangel.

## 1. Wann
Jede Anfrage nach Markentrix-Werbevideo, Ad-Video, Reel, TikTok, UGC, Hook-Test oder Varianten. Nicht für Kundenprojekte (andere CI/Claims erfragen).

## 2. Hard Gates
1. Kein erfundener Kunde: Die generierte Person ist Host/Erklärer, nie Kunde/Handwerksmeister mit Erfolgsstory. Keine erfundenen Zitate, Bewertungen, Vorher-Nachher-Zahlen, Fallstudien.
2. Nur freigegebene Aussagen (Abschnitt 5). CI-Beispielzahlen (z. B. „+142 %“) sind Gestaltungsbeispiele, nie Behauptung.
3. Erwachsene generierte Person (21+), keine reale/öffentliche Person, keine Stimmimitation. Ausnahme: Kitz mit eigenem Foto, Stimme nie geklont.
4. Sprache Deutsch: im Dialog-Prompt steht „Die Person sagt wörtlich auf Deutsch: „…““ (build_dialogue_prompt erledigt das). Wahrheits- und Sicherheitsregeln dieses Skills gelten immer.
5. Kein Text in der Generierung; Text, Logo, Endcard, Untertitel erst nach dem Render (CI-Schrift).
6. KI- und Werbung-Kennzeichnung nach Abschnitt 9 Pflicht.
7. Nach außen nur Markentrix: nie Modell-/Tool-Namen, Request-IDs oder „mit Claude/Higgsfield erstellt“ in Video, Caption, Mail, Dokument. Absender immer „Markentrix“ / „Ihr Markentrix-Team“. Erlaubt: „Dieses Video wurde mit KI-Unterstützung erstellt.“
8. Keine Telefon-/Kontaktdaten erfinden; nur markentrix.de · info@markentrix.de · Celle, Niedersachsen.

## 3. Marke (CI)
- Positionierung: KI- und Performance-Marketing-Agentur für lokale Unternehmen; Claim „Automatisierung. Werbung. Wachstum.“; Sales-Claim „Mehr Anfragen. Weniger Aufwand.“ (Slogan, nie Garantie).
- Wirkung: modern, premium, digital, strategisch, messbar, professionell, präzise, seriös. Nie: verspielt, billig, generisch, Canva-Agentur, Krypto-Look, Neon, KI-Roboter, Dark-First.
- Ton: Direkt statt laut. Fachlich statt generisch. Nutzenorientiert statt verspielt.
- Bausteine: „Schöne Posts sind kein Marketing. Systeme erzeugen Wachstum.“ · „Sichtbarkeit allein reicht nicht. Entscheidend ist, ob daraus Anfragen entstehen.“ · „KI ist kein Selbstzweck.“ · „Ein System statt Einzelmaßnahmen.“
- Farben: Soft White #F8FAFC / Pure White #FFFFFF (~65 %), Graphite Navy #0B1020 / Black #05070B (~18 %), Cyan #28C7F7 / Blue #1E9BFF (~12 %), Violet #8B5CF6 (~4 %), Magenta #D85CFF (~1 %), Cool Gray #B8C0CC, Muted Gray #667085.
- Typo: Space Grotesk Bold/SemiBold (Headlines), Inter Regular/Medium (Text), echte Schriftdateien.
- Signature: Wachstumskurve, max. EIN dominantes Element pro Fläche.
- Logo: Light Standard, Dark nur bewusste Kontrastfläche; Schreibweise „Markentrix“; Schutzraum = Höhe „M“; nie verzerrt/gedreht/umgefärbt/Schatten; min. 120 px (Bildmarke 32 px).
- CTA: genau eine, Cyan→Blue; Standard „Marketing-Check anfragen“.

## 4. Zielgruppe & Anrede
Inhaber/GF lokaler Betriebe in Celle und Region (Handwerk, Werkstätten/Kfz, Praxen, Gastro, Handel). Erlaubte Schmerzpunkte (Beobachtung, keine Behauptung über eine Person): Anfragen gehen unter, Telefon klingelt bei der Arbeit, Nachfassen kostet Zeit, Bewertungen vergessen, Social „nebenbei“, Werbung ohne Anfragen.
Anrede je Branche: „Du/ihr“ für Handwerk, Werkstätten, Kfz, Gastro, Einzelhandel; „Sie“ für Praxen, Kanzleien/Steuer, Immobilien, B2B, 50+ oder formell; unklar = „Sie“. Eine Anrede pro Video. Ein Spot = eine Branche + ein Schmerzpunkt.

## 5. Allowlist (Wortlaut möglichst verbatim)
Marke: „KI-Automatisierung & Social-Media-Werbung für lokale Unternehmen.“ · „Automatisierung. Werbung. Wachstum.“ · „Mehr Anfragen. Weniger Aufwand.“ · „Markentrix automatisiert Marketing und macht lokale Unternehmen sichtbar.“ · Sitz Celle.
Leistungen (CI): KI-Automatisierung (Anfrage-Vorqualifizierung, automatische E-Mail-Antworten, Bewertungsautomatisierung, Termin-Workflows, Wissensdatenbanken, Chatbot-Konzepte); Social-Media-Werbung (Meta-Ads-Strategie, Lead-Kampagnen, Retargeting, A/B-Tests); Lokale Sichtbarkeit (Google-Profil, lokale SEO-Grundlagen, Bewertungsstrategie); Content & Werbemittel.
Preise (Stand 01.10.2026, netto zzgl. USt; nur in ausdrücklichen Preis-Spots, nur eine Zahl, mit „netto“, vorher gegen aktuelle Preisliste prüfen): KI-Kundenkommunikation ONE 1.490 € + 349 €/Mon., BUSINESS 2.490 € + 699 €/Mon. (Telefonagent ab BUSINESS), KOMPLETT 3.490 € + 1.190 €/Mon.; in allen Paketen Einrichtung, Gesprächsleitfäden, Wissensbasis, Kalenderanbindung, Testbetrieb vor Livegang, Datenschutzdokumentation, fester Ansprechpartner. Websites ab 1.290 €, CI ab 1.290 €, SOCIAL MEDIA 749 €/Mon., LOCAL VISIBILITY 449 €/Mon.; 12 Monate Mindestlaufzeit, danach monatlich kündbar; Kombivorteil 500 € Nachlass. In Lead-Ads standardmäßig KEINE Preise.
NICHT erlaubt ohne schriftliche Freigabe: Ergebnis-/Prozentzahlen, „garantiert“, „Platz 1 bei Google“, „24/7“, „spart X Stunden“, Kundennamen/-logos, Bewertungen/Sterne, „Anrufer merken nicht, dass es KI ist“, Wettbewerbervergleiche, Rechts-/Steuer-/Heilversprechen, falsche Verknappung. Ohne Beleg: Fähigkeit beschreiben („Wir bauen …“), kein Ergebnisversprechen.

## 6. Videotypen
Standard = Typ A.
- A Problem → System (Host in Kamera, 15 s, Lead-Ad) – `clip` mit seedance2-ref, 1 Clip
- B Mythos-Buster (15–20 s) – `clip`, 1 Clip (bis 15 s) oder 2 Clips + `concat`
- C System erklärt (Host + CI-gerenderte Workflow-/Anfrage-Karten als Overlay) – `clip` + `overlay_png` mit Karten aus dem CI-Renderer
- D Seiten-Tour (echte Screenshots markentrix.de per Playwright, nie generierte UI) – Screens als Standbilder/Ken-Burns per ffmpeg, optional Host-Intro per `clip`
- E Paket-Spotlight (ein Paket, ein Preis) – Preisregel beachten
- F Gründer-Format (Kitz, eigenes Foto als `image_urls`, bestätigtes Skript, Stimme nie geklont)
- G Proof/Case – nur mit echten, freigegebenen Zahlen und Kundenerlaubnis, sonst nicht produzieren

## 7. Skript & Hook
Struktur 15 s (~32–36 Wörter, Obergrenze ~38, ~2,2–2,5 Wörter/s): (1) Hook 0–3 s, ≤8 Wörter, Schmerzpunkt/Mythos, kein „Hallo, ich bin“, kein Markenname im ersten Satz; (2) Wendung 3–6 s, eine Einsicht; (3) System 6–12 s, 1–2 Bausteine aus Abschnitt 5, Nutzen vor Technik, keine Tool-Namen (n8n/Make); (4) CTA 12–15 s, ein Satz, eine Handlung.
Kurze aktive Sätze; keine Floskeln („innovativ“, „ganzheitlich“, „next level“, „Gamechanger“), keine Superlative, kein Clickbait; Zahlen ausgeschrieben; Skript = einzige Quelle der Untertitel.
Aussprache: „Markentrix“ im Skript ggf. als „Mar-ken-triks“ absichern; „KI“ als „Ka-I“ schreiben und im Testclip per Transkription prüfen; Fremdwörter meiden. Bei neuer Serie immer erst Testclip (5 s, günstig): Aussprache + Lippensync prüfen, bei Problemen Skript kürzen statt Modell wechseln.
Hooks (pro Branche anpassen): Handwerk/Werkstatt „Das Telefon klingelt – und Sie stecken unterm Auto.“ · „Anfragen kommen. Und gehen wieder unter.“ · „Schöne Posts bringen keine Aufträge.“ Praxis/Dienstleister „Die Anfrage liegt seit gestern im Postfach.“ · „Sichtbar sein reicht nicht.“ Gastro/Handel „Jeden Tag derselbe Post – und niemand reagiert?“ · „Bewertungen schreiben sich nicht von allein.“ Mythos „Schöne Posts sind kein Marketing.“ · „KI ist kein Selbstzweck.“
Beispiel Typ A (Du, Handwerk, 15 s): „Anfragen kommen. Und gehen wieder unter. Sichtbarkeit allein reicht nicht – entscheidend ist, ob daraus Anfragen werden. Wir verbinden Werbung, Automatisierung und lokale Sichtbarkeit zu einem System statt zu Einzelmaßnahmen. Hol dir deinen Marketing-Check.“

## 8. Bild, Creator, Ton
Look White/Light Premium: natürliches Tageslicht, helle Räume (Büro mit Fensterlicht, aufgeräumter Werkstatt-Eingang, Laden), ruhiger Hintergrund, Smartphone-Authentizität, korrekte Hände/Objekte. Cyan/Violet nur dezent in Requisiten/Karten; kein Neon, Glow, Roboter, Hologramm, Sci-Fi-UI, Stockfoto-Look, Dark-Look.
Markentrix-Host: eine feste generierte erwachsene Person (ca. 30–40), gepflegt, bodenständig-professionell, Navy/Weiß/Grau ohne Logos/Schrift, kein Lanyard, keine Badges, keine fremden Marken oder Bildschirme im Hintergrund (SOUL V2 erzeugt sonst gern Lanyards und Logos: Host-Bild vor Freigabe darauf prüfen, bei Mangel neu erzeugen, kostet Bruchteile eines Cents). Aussehen beim ersten Lauf festlegen und danach festschreiben: Datei in `output/host/`, Metadaten in `host-meta.json`, nach Freigabe Pfad und Request-ID in claude/creative-system/host-referenz.md dokumentieren und in Serien nie neu generieren; in jedem `clip` dasselbe Host-Bild als Referenz. Auftreten ruhig, direkt, leichtes Lächeln, kein Moderatorenpathos. Sprache Hochdeutsch, neutral bis leicht norddeutsch, kein Dialekt, kein englischer Akzent. Setting passend zur Branche, aber immer Host als Erklärer.
Ton: nativer Modell-Ton (Sprache dominant) oder eigene Spur über `audio_urls`; kein lizenzpflichtiger Trendsound in Ads; dezentes rechtefreies Bett nur in der Nachbearbeitung; einheitliche Lautheit (ffmpeg loudnorm, Ziel −16 LUFS).

## 9. Recht & Plattform (kein Rechtsrat, Stand prüfen)
- UWG: keine unbelegten Versprechen, keine fingierten Erfahrungsberichte, Werbung klar erkennbar.
- KI-Kennzeichnung: Plattform-Label für KI-Inhalte aktivieren (TikTok, Meta) und im Post „Dieses Video wurde mit KI-Unterstützung erstellt.“; Transparenzpflichten nach EU-KI-Verordnung Art. 50 vor Veröffentlichung auf aktuellen Stand prüfen.
- Paid = Plattform-Kennzeichnung Anzeige/Werbung; organisch keine getarnte Kundenstimme.
- KI-Telefonagent nie so bewerben, als wüssten Anrufer nicht, dass sie mit einer KI sprechen.
- DSGVO: keine echten Kundendaten, Kennzeichen, Gesichter, Posteingänge; Karten synthetisch.
- Branchenrecht: Praxen/Heilmittelwerbegesetz keine Heilversprechen; Steuer/Recht keine Beratungsversprechen.
- Musik, Schriften, Fremdbilder nur lizenzfrei oder eigen.

## 10. Ablauf
1. Briefing prüfen (Abschnitt 11); unbeaufsichtigt: Annahmen in einem Satz nennen und weitermachen.
2. Projektquellen prüfen: Preisliste-Stand, CI-Version, host-referenz.md. `python -m higgsfield_api check`.
3. Skript schreiben, Wörter zählen, gegen Allowlist prüfen; drei Hook-Varianten, eine produzieren, zwei vorhalten.
4. Host: gespeichertes Host-Bild nutzen; sonst einmalig `python -m higgsfield_api host`, Bild ansehen (Lanyard/Logos/Text?), freigeben lassen, dokumentieren.
5. Kosten nennen: `python -m higgsfield_api clip <host> "<Skript>" --duration 15 --dry-run`. Bei neuer Serie zuerst Testclip mit 5 s und den schwierigen Wörtern (Markentrix, KI).
6. Rendern: `python -m higgsfield_api clip <host> "<Skript>" --duration 15 --name "MKT_VIDEO_A_<Branche>_H1_15s_v1"`; 15 s = 1 Clip; 20–30 s = 2 Clips (gleiches Host-Bild, Skript geteilt) + `post.concat`. Immer 9:16, 1080p, Deutsch.
7. Frozen-Frame-QA (Abschnitt 12): `python -m higgsfield_api frames <clip>` und die PNGs ansehen; Transkription gegen Skript; nur fehlerhafte Clips neu rendern (gleiches Host-Bild, Skript ggf. kürzen).
8. Brand-Layer (Abschnitt 13) mit `post.py` + CI-Renderer.
9. Post-Paket und Varianten (Abschnitt 14), im Projekt ablegen, Auslieferung in einem Satz.

## 11. Intake
Eine gebündelte Rückfrage, nur was fehlt: (1) Branche, (2) Angebot/Paket oder Marketing-Check, (3) Videotyp (Standard A), (4) Dauer (Standard 15 s; 10/20/30 s), (5) Anrede-Abweichung, (6) Preis ja/nein (Standard nein). Nie nach Technik fragen, nie nach Dingen, die in CI/Preisliste stehen.

## 12. Qualitäts-Gate (ein Fehler = Nacharbeit)
1. Jede Aussage in Allowlist, keine Zahl ohne Beleg, Preis nur mit „netto“.
2. Ein Creator, ein Gesicht, ≤2 Hände, keine Doppel-Lippen, keine Drift; Gesicht entspricht dem Host-Bild.
3. Aussprache sauber, „Markentrix“ korrekt, Lippensync ok (Mid-Word-Frames); Transkription deckt sich mit dem Skript.
4. Kein eingebackener Text, keine fremde Marke, kein Lanyard/Badge.
5. Hook in 1–2 s verständlich, eine Kernbotschaft, ein CTA.
6. Look hell und natürlich, kein Dark-First/Neon/Roboter.
7. Untertitel exakt aus finalem Audio, Rechtschreibung geprüft.
8. Safe Area 9:16: nichts Wichtiges in oberen 240 px und unteren 330 px; Text/Logo nie randnah.
9. Logo korrekt, Endcard CI-konform.
10. KI- und Werbung-Kennzeichnung im Post-Paket.
11. Ein Signature-Element, Weißraum auf Endcard.
12. Keine Tool-/Modellnamen oder Request-IDs in Datei, Name, Caption.
Report: „bestanden“ oder konkrete Mängelliste in einem Satz; was nicht selbst prüfbar war (z. B. Hörprüfung ohne Transkription), ausdrücklich als „Sichtprüfung offen“ nennen.

## 13. Brand-Layer (Nachbearbeitung, lokal mit ffmpeg)
- Hook-Plate (empfohlen für Ads): Space Grotesk Bold, Navy auf hellem Band oder Weiß mit feinem Rand, ab y ≥ 260 px, max. 2 Zeilen, nur erste 2–3 s; als PNG aus dem CI-Renderer, einblenden mit `post.overlay_png(start=0, end=3, y="260")`.
- Untertitel: Inter/Space Grotesk, groß, hoher Kontrast, oberhalb der unteren 330 px, max. 2 Zeilen, Schlüsselwort optional Cyan #0E8FC4 auf hell; `post.make_srt` als Startpunkt, Zeiten gegen die Transkription anpassen, dann `post.burn_subtitles`.
- Karten (Typ C): aus ci-design-system.mjs gerendert (cards, stat), Light-Theme, 1-px-Rahmen, keine harten Schatten, synthetische Inhalte, ~1,2–1,5 s je Karte, nicht während Hook und CTA; einblenden mit `post.overlay_png`.
- Endcard (immer, 2–2,5 s, 1080×1920, page({format:'story', theme:'light'})): Soft White, ~65 % Weißraum, Headline „Mehr Anfragen. Weniger Aufwand.“, Subline „KI-Automatisierung & Social-Media-Werbung für lokale Unternehmen.“, genau eine CTA „Marketing-Check anfragen →“ Cyan→Blue, Logo hell dezent, URL markentrix.de, ggf. kleine Wachstumskurve als einziges Signature-Element, alles in Safe Area; anhängen mit `post.append_endcard`, Ton klingt aus.
- Renderer-Setup: claude/creative-system/README.md (Fonts via @fontsource, Logos aus Projektdateien, Playwright/Chromium). Master ohne Text getrennt aufheben.

## 14. Lieferumfang
1. Finales Video (9:16 MP4 mit Endcard) + sauberer Master ohne Text.
2. Post-Paket: Primärtext (Hook vorn, ≤ ~125 sichtbare Zeichen), Headline (≤40 Zeichen), Beschreibung, CTA-Button („Jetzt anfragen“/„Mehr dazu“), 3–5 Hashtags (#Celle #KIAutomatisierung #LokalesMarketing + Branche), Pinned-Kommentar, „Anzeige/Werbung“ und „Dieses Video wurde mit KI-Unterstützung erstellt.“; Absender Markentrix.
3. A/B-Matrix: erster Test 3 Hooks × 1 Creator × 1 CTA; danach Gewinner mit variiertem CTA/Setting; immer nur EINE Variable pro Test.
4. Messgrößen: Hook-Rate, Halte-Rate, Klickrate, Kosten pro Lead; Entscheidung nach realen Daten.
5. Benennung: MKT | VIDEO | <Typ> | <Branche> | H<Nr> | <Dauer>s | v<Nr> | <JJJJ-MM-TT>
6. Ablage: Skript, Allowlist-Sätze, Request-IDs (intern), Kosten laut Schätzung, Ergebnis und Gewinner-Hooks in claude/creative-system/video-log.md vermerken.

## 15. Stolperfallen
- Modell spricht Englisch oder weicht vom Text ab: Dialog steht in Anführungszeichen mit „sagt wörtlich auf Deutsch“; bei Abweichung Skript kürzen, Sätze trennen, nicht beschleunigen.
- SOUL V2 liefert Lanyards, Badges, Bildschirme mit Logos: Host-Bild immer ansehen, bei Mangel mit neuem Seed neu erzeugen.
- Zu bildhafte Branchen-/Produktprompts: Modell erfindet Schilder/Logos; Hintergründe neutral, keine lesbaren Schilder.
- Screens/Karten nie generieren; nur CI-Renderer oder echte Screenshots.
- Ein Format = ein Schmerzpunkt.
- CI-Beispielzahlen (+142 %) nie verwenden.
- Preisliste ändert sich: vor Preisnennung Stand prüfen.
- Ergebnis-URLs laufen ab: alles sofort herunterladen und im Projekt ablegen.
- Guthaben leer = HTTP 403: in console.higgsfield.ai aufladen, Nutzer informieren, nicht auf den Connector ausweichen.
