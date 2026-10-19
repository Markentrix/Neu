# Markentrix Server-Paket: Anleitung

Dieses Paket richtet auf deinem Hetzner-Server alles Neue mit **einem Befehl** ein:

- **PostgreSQL-Datenbank** mit fertiger Struktur (66 Tabellen): Kunden mit Kundennummer, Zugänge, Preiskatalog (Preisliste Stand September 2026) und Buchungen, Kundenbereich, Konfiguration und Prompts, Wissensbasis und Agentenläufe, Vertrieb, Akquise und Lead-Finder, Kommunikation, Datenschutz (Einwilligungen, Auskunft, Löschung) und Qualität (Befunde, Maßnahmen, Ausnahmeregister, Alarme). Jeder Kunde sieht nur seine eigenen Daten (getestet). Kein Supabase.
- **n8n** (deine Workflows), mit eigener Datenbank
- **Server-Dashboard** unter `panel.deine-domain.de` (nur lesend): zeigt Dienste, Websites, Demos, Speicher und Sicherungen
- **Tägliche Sicherung** um 03:15 Uhr, 14 Tage Aufbewahrung
- **mkctl**: kleines Werkzeug für Demos, Kunden-Websites, Updates und Sicherungen
- **Caddy** (HTTPS) nur, wenn noch keiner läuft. Ein vorhandener Caddy wird **nicht verändert**.

## Schritt 1: DNS-Einträge anlegen

Bei deinem Domain-Anbieter (aktuell Squarespace) vier neue **A-Einträge** anlegen, Ziel ist die IP deines Servers (5.75.146.212):

`n8n`, `panel`, `portal`, `demo` (also z. B. `n8n.markentrix.de`)

Die bestehenden Einträge für markentrix.de und www bleiben, wie sie sind.

## Schritt 2: Paket auf den Server bringen

Auf deinem Computer im Terminal (dort, wo die Datei `markentrix-server.tar.gz` liegt):

```
scp markentrix-server.tar.gz root@5.75.146.212:/root/
ssh root@5.75.146.212
```

## Schritt 3: Installieren

Jetzt auf dem Server:

```
tar xzf markentrix-server.tar.gz
cd markentrix-server
sudo bash install.sh
```

Das Skript fragt zwei Dinge (Hauptdomain, E-Mail für die Zertifikate), dort reicht jeweils Enter, wenn die Vorgabe stimmt. Der erste Start lädt einige GB und dauert 5 bis 15 Minuten.

Am Ende steht eine Zusammenfassung mit Adressen und Passwörtern auf dem Bildschirm. **Speichere sie sofort in einem Passwortmanager.**

Bricht das Skript ab, schick mir einfach die letzten Zeilen. Es kann gefahrlos erneut gestartet werden.

## Wenn schon ein Caddy läuft (z. B. für markentrix.de)

Das Skript erkennt das, lässt ihn unverändert und schreibt die nötigen Zeilen in die Datei `/opt/markentrix/caddy-zusatz-fuer-bestehenden-caddy.txt`. Diese drei Blöcke müssen in die vorhandene Caddyfile kopiert werden, danach Caddy neu laden. Das machen wir dann gemeinsam, bevor du etwas veränderst.

## Alltag: mkctl

```
mkctl status                              Überblick
mkctl backup                              Sicherung jetzt
mkctl psql                                Datenbank-Konsole
mkctl migrate                             Datenbankstruktur anlegen/aktualisieren
mkctl demo-add anadolu                    neue Demo unter https://demo.markentrix.de/anadolu/
mkctl site-add kunde.de --kunde "Name"    Kunden-Website mit eigener Domain
mkctl update                              Sicherung, dann alles aktualisieren
mkctl n8n-version 1.2.3                   n8n gezielt auf eine Version setzen (mit Sicherung davor)
mkctl mail-check                          SPF/DKIM/DMARC der Absender-Domain prüfen
mkctl ssh-haerten                         Passwort-Login per SSH abschalten (nur mit Schlüssel)
mkctl help                                alle Befehle
```

Eigene Dateien einer Website kopierst du mit `--from /pfad/zum/ordner` hinein.

## Sicherheit

- Alle Dienste sind nur über HTTPS und Caddy erreichbar. Die Datenbank hört nur auf dem Server selbst.
- Es gibt keine öffentliche Registrierung. Kunden legst du selbst an.
- Empfohlen: In der Hetzner Cloud Console eine **Firewall** anlegen, die nur die Ports 22, 80 und 443 erlaubt.
- `/opt/markentrix/.env` enthält alle Schlüssel. Ohne sie lässt sich nichts wiederherstellen. Die tägliche Sicherung legt eine Kopie ab, die Sicherungen liegen aber auf demselben Server. Eine Kopie außerhalb des Servers richtest du mit `mkctl offsite-setup` ein (siehe „Sicherheit und Überwachung“).

## Das Portal benutzen

**Admin (du):** `https://portal.deine-domain.de`, Login mit der E-Mail aus der Installation. Das Passwort steht am Ende der Installation. Neues Passwort jederzeit: `mkctl admin-reset deine@mail.de`.

Kunde anlegen: *Neuer Kunde* → Firma, E-Mail, Paket → „Einladungslink erzeugen". Den Link schickst du dem Kunden (7 Tage gültig). Er legt damit sein Passwort fest und sieht nur seine eigenen Daten.

Im Kunden stellst du per **Schalter** ein, welche Module er sieht (KI-Assistent, Anfragen & Termine, Wochenangebote ...). Unter *Buchungen* hältst du gebuchte Pakete samt Preis fest.

**Wochenangebote:** Bei einem Kunden mit Website: Website im Admin anlegen und einmal auf dem Server `mkctl site-add kunde.de` ausführen. Modul „Wochenangebote" einschalten. Der Kunde lädt PDF/JPG/PNG hoch, danach liegt es sofort unter `https://kunde.de/angebote/`.

**Mehrsprachige Angebotsseite:** Pro Website stellst du im Admin (Kunde öffnen → Websites → „Sprachen der Angebotsseite“) ein, welche Sprachen erscheinen: Deutsch (immer), Türkisch, Englisch, Arabisch. Der Kunde pflegt unter Wochenangebote zusätzlich **Angebote mit Preis, Events, Hinweise und „Heute geschlossen“**, jeweils mit Titel und Text pro Sprache. Fehlt eine Übersetzung, zeigt die Seite den deutschen Text. Die Seite erkennt die Browsersprache des Besuchers, es gibt Knöpfe zum Umschalten, Arabisch läuft von rechts nach links. Einträge mit Zeitraum verschwinden nach Ablauf automatisch, „Heute geschlossen“ gilt nur an den eingetragenen Tagen. Die Datei (PDF/Bild) und die Texte stehen zusammen auf `https://kunde.de/angebote/`. Nach dem Update einmal `mkctl site-add` ist nicht nötig, die Ordner bleiben bestehen. Mit dem Knopf **„Aus Deutsch übersetzen“** füllt das System leere Felder (Titel und Text) in den anderen Sprachen automatisch, der Kunde prüft kurz und speichert. Das braucht den KI-Schlüssel unter Einstellungen → KI, die Kosten stehen pro Kunde unter Kosten. Höchstens 40 Übersetzungen pro Kunde und Tag. Ohne Schlüssel trägt der Kunde die Texte selbst ein.

**KI-Chat anbinden (später):** In `/opt/markentrix/.env` `CHAT_WEBHOOK_URL` (n8n-Webhook) und `CHAT_WEBHOOK_SECRET` eintragen, dann `mkctl restart portal`.

**Vertriebler:** Menü *Vertriebler* → anlegen, Kunden im Kunden unter „Vertriebler" zuordnen, Provisionen freigeben und als ausgezahlt markieren. Leads: Menü *Leads*, Status pflegen, einem Vertriebler geben, „Zum Kunden machen".

**Preise:** Menü *Preise & Konditionen*: neue Preise gelten ab einem Datum, alte Buchungen behalten ihren Preis. Provisionsregeln stehen als Entwurf da und gelten erst nach deiner Freigabe.

**Datenschutz & Qualität:** offene Alarme, Freigaben, DSGVO-Anfragen, Workflow-Fehler und Befunde an einem Ort.

## Was noch offen ist

1. **Hetzner Cloud Firewall** (nur Ports 22, 80, 443) in der Hetzner-Konsole anlegen.
2. **n8n-Workflows:** Aus n8n Cloud exportieren und im neuen n8n importieren, Zugangsdaten neu verbinden.
3. **markentrix-core:** Im Repo liegt noch kein Code, deshalb nicht Teil dieses Pakets.
4. **Externe Sicherung einrichten** (siehe unten, `mkctl offsite-setup`).
5. **Firmendaten, SMTP und KI-Key** unter Einstellungen eintragen, Impressum und Datenschutz juristisch prüfen lassen.

## E-Mail-Versand, KI-Chat, Vertriebler-Login, Provisionen

**Einstellungen** (Admin → Einstellungen)
- *E-Mail-Versand (SMTP)*: Server, Port, Verschlüsselung (meist STARTTLS/587), Benutzername, Passwort und Absender deines Postfachs (z. B. info@markentrix.de) eintragen, speichern, dann „Testmail senden". Danach gehen Einladungen und „Passwort vergessen"-Mails automatisch raus. Das Passwort wird verschlüsselt gespeichert.
- *KI-Assistent*: API-Key aus der Anthropic-Konsole (console.anthropic.com) eintragen. Modell ist vorgegeben (günstig), dazu ein Tageslimit pro Kunde. Ohne Key nutzt der Chat weiter den n8n-Webhook (falls eingerichtet). Abgerechnet wird pro Nutzung direkt bei Anthropic.

**Vertriebler-Login**: Admin → Vertriebler → Name anklicken → „Portal-Zugang" → E-Mail eintragen → „Einladung erzeugen". Der Vertriebler bekommt die Mail, legt sein Passwort selbst fest und meldet sich unter portal.markentrix.de an (landet automatisch im Partnerportal). Er sieht nur seine eigenen Kunden, Leads und Provisionen. Sperren/Freigeben geht am selben Ort.

**Provisionen**: Zuerst unter Preise & Konditionen die Provisionsregel(n) „laufend" freigeben. Dann Admin → Vertriebler → „Provisionen berechnen": Monat wählen → Vorschau → Anlegen. Doppelte Einträge werden nie angelegt. Der Vertriebler sieht seine Beträge sofort; Freigeben/Auszahlen markierst du beim Vertriebler.

**Referenzkunden**: Beim Anlegen (oder später in den Stammdaten) „Referenzkunde" anhaken und eintragen, was der Kunde bekommt (z. B. Website, Agent). Referenzkunden werden wie alle Kunden verwaltet (Module, Websites, Portal-Zugang, Daten), Buchungen bekommen automatisch 0 €, sie zählen nicht in „Monatlich (gebucht)" und lösen keine Vertriebler-Provision aus. In der Kundenliste sind sie markiert und filterbar. „Darf als Referenz genannt werden" nur anhaken, wenn das Einverständnis des Kunden vorliegt.

## Firmendaten, Impressum, Datenschutz

Admin → Einstellungen → **Firmendaten**: Name, Inhaber, Anschrift, E-Mail, Telefon, Steuernummer oder USt-IdNr, Bankverbindung, Zahlungsziel, Umsatzsteuersatz und ob du **Kleinunternehmer (§ 19 UStG)** bist. Ohne Steuernummer oder USt-IdNr lässt das Portal keine Rechnung ausstellen. Aus diesen Daten entstehen auch Impressum (`/impressum`) und Datenschutzerklärung (`/datenschutz`), beide ohne Login erreichbar und in der Anmeldeseite verlinkt. Die Texte sind Standardvorlagen: **bitte einmal von einer Anwältin oder einem Anwalt prüfen lassen**. Eigene Texte kannst du in den Einstellungen hinterlegen. Die Vorlage für den Auftragsverarbeitungsvertrag (AVV) steht auch als Text unter `docs/AVV-Vorlage.md`; die im Portal erzeugte PDF-Fassung nutzt denselben Inhalt (siehe nächster Abschnitt).

## Auftragsverarbeitungsvertrag (AVV) pro Kunde

Jeder Kunde braucht einen unterschriebenen AVV, bevor du seine Daten verarbeitest. Im Portal beim Kunden → Karte **Auftragsverarbeitungsvertrag**:
1. „Neuen AVV erstellen“, dann **Vertrag (PDF)** öffnen: Kundenname, Anschrift und deine Firmendaten sind eingesetzt.
2. **Per Mail senden** schickt das PDF an die Kunden-E-Mail (Versand muss eingerichtet sein).
3. Unterschrieben zurück? Datei wählen, Unterschriftsdatum eintragen, **Ablegen** (PDF, Scan oder Foto, max. 6 MB). Der Onboarding-Punkt „AVV“ wird automatisch erledigt.
4. Der Kunde sieht den abgelegten Vertrag in seinem Portal unter **Datenschutz-Vertrag** (nur Inhaber-Zugänge).
5. In der Admin-Übersicht und in der Kundenliste steht „AVV fehlt“. Drei Tage nach Anlage ohne AVV bekommst du eine Mail, danach höchstens einmal pro Woche.

Wichtig: Unter Einstellungen → **AVV: Unterauftragsverarbeiter** die Liste prüfen und vervollständigen (E-Mail-Anbieter, Telefonie-Dienst …). Der Vertragstext ist eine Vorlage und muss einmal juristisch geprüft werden. Abgelegte, unterschriebene Fassungen lassen sich nicht löschen, nur Entwürfe.

## Zwei-Faktor-Anmeldung (2FA)

Jeder Zugang kann unter Einstellungen eine Authenticator-App koppeln (QR-Code scannen, Code eingeben). Dabei entstehen 10 Notfallcodes, die nur einmal angezeigt werden. **Für den Admin dringend empfohlen**, bis dahin zeigt das Portal einen Hinweis. Hat jemand das Handy verloren, setzt der Admin die 2FA im Zugang zurück (Kunde: Portal-Zugang, Vertriebler: Portal-Zugang).

## Benachrichtigungen und Monatsbericht

Voraussetzung: E-Mail-Versand ist eingerichtet. Das Portal prüft jede Minute im Hintergrund und mailt dem Kunden bei **neuen Anfragen** und kurz vor **Terminen** (Voreinstellung 24 Stunden). Kunden schalten das unter Einstellungen einzeln ab. Am Monatsanfang erstellt das Portal automatisch den **Monatsbericht** (PDF: Anfragen, Termine, Anrufe, Nachrichten, Chat, Agent-Läufe …) und mailt ihn; Referenz- und aktive Kunden bekommen ihn, Admin kann ihn pro Kunde auch von Hand erstellen. Fehler in Workflows melden sich per Mail an dich (Einstellungen → Benachrichtigungen, Alarm-Adresse).

## Onboarding-Checkliste

Beim Anlegen eines Kunden entsteht automatisch eine Checkliste (Vertrag, Zugang, Website, Wissen, Module …). Manches haken Portal und Server selbst ab (Zugang eingerichtet, Website live, Wissen erfasst). In der Übersicht siehst du alle Kunden mit offenen Punkten. Eigene Punkte kannst du ergänzen.

## Angebote und Rechnungen

Beim Kunden → Angebote & Rechnungen: Vorlage aus den Buchungen übernehmen, Positionen anpassen, **ausstellen** (vergibt eine lückenlose Nummer, danach nicht mehr änderbar), als PDF herunterladen oder per Mail senden. Rechnungen enthalten einen GiroCode (QR für die Banking-App). Fehler korrigierst du mit einer **Stornorechnung**, nicht durch Ändern. Mahnungen (3 Stufen) gibt es per Knopf, „Bezahlt" setzt du von Hand. Kunden sehen und laden ihre Belege im Portal und können Angebote annehmen.

Wichtig:
- Du hattest dich für **sevDesk** als Buchhaltung entschieden. Das Portal erstellt Rechnungen, die du dort weiterverwenden kannst: Angebote & Rechnungen → „Rechnungen als CSV exportieren". Ob du Rechnungen im Portal oder direkt in sevDesk erstellst, solltest du **einheitlich** halten (gleiche Nummernkreise!).
- **E-Rechnung:** Für Rechnungen zwischen Unternehmen (B2B) gilt in Deutschland nach und nach eine Pflicht zur strukturierten E-Rechnung (ZUGFeRD/XRechnung). Das Portal erzeugt bisher nur PDF-Rechnungen. Bitte mit der Steuerberatung klären, ab wann das für dich gilt; Kleinunternehmer sind ausgenommen.
- Referenzkunden bekommen keine Rechnungen.

## Vertriebler: Abrechnung, Verlängerung, Rückbuchung

- **Provisionsabrechnung (PDF)** pro Monat: Admin → Vertriebler → Name → „Abrechnung als PDF". Der Vertriebler lädt sie selbst im Partnerportal (Provisionen → Pro Monat). Es ist eine Abrechnung, keine Rechnung im steuerlichen Sinn.
- **Verlängerungsprovision**: Wird bewusst von Hand erfasst („Verlängerung erfassen", Buchungs-ID und Monat). Betrag = Prozentsatz der freigegebenen Regel × Monatsbetrag × 12 Monate. Das ist meine Auslegung deiner Regel (5 %): bitte prüfen, bevor du die Regel freigibst.
- **Nachlauf**: Wird ein Vertriebler auf „beendet" gesetzt, laufen seine Provisionen noch so viele Monate weiter, wie in `provision.nachlauf_monate` steht (Standard 6).
- **Rückbuchung**: Bei einer bereits ausgezahlten Provision „Zurückbuchen" wählen, die negative Zeile wird im gewählten Monat verrechnet.

## Kosten pro Kunde

Im Kunden steht die Karte „Kosten (KI-Chat) pro Monat" mit Tokens, Kosten in Euro und dem Anteil am Monatsumsatz. Die Preise je 1 Mio. Tokens stehen unter Einstellungen → KI-Assistent (Voreinstellung 3 € / 15 €); bitte mit der aktuellen Anthropic-Preisliste abgleichen. Andere Kosten (Telefonie, Domain, Werbung …) trägst du in derselben Karte unten von Hand ein (Kostenart, Betrag, optional Datum); sie fließen in die Monatssumme ein und werden zusätzlich nach Kostenart aufgeteilt angezeigt.

## Team-Zugänge, Branding, App

- **Mehrere Zugänge pro Kunde**: Der Kunde lädt im Menü **Team** selbst Kolleginnen und Kollegen ein. Rollen: *Inhaber* (alles), *Mitarbeiter* (alles außer Team und Rechnungen), *Nur ansehen*. Der Admin sieht die Rolle in der Zugangs-Tabelle des Kunden.
- **Branding**: Beim Kunden Logo (PNG/JPG, max. 400 KB) und Akzentfarbe setzen; der Kunde sieht beides in seinem Portal.
- **Als App installieren**: Das Portal ist installierbar (Handy: Browser-Menü → „Zum Startbildschirm“; Chrome/Edge am Rechner: Installieren-Symbol in der Adressleiste). Es werden keine Daten auf dem Gerät zwischengespeichert.

## Sicherheit und Überwachung

- **Externe Sicherung**: Eine Hetzner Storage Box bestellen, dann auf dem Server `mkctl offsite-setup u123456@u123456.your-storagebox.de markentrix`. Der Befehl zeigt einen öffentlichen Schlüssel, den du in der Storage-Box-Verwaltung hinterlegst; danach `mkctl offsite-test`. Die Sicherungen werden verschlüsselt hochgeladen. **Die Datei `/opt/markentrix/offsite/passphrase` außerhalb des Servers aufbewahren** (Passwortmanager), sonst sind die Sicherungen nicht lesbar.
- **Wiederherstellungstest**: läuft sonntags automatisch (`mkctl restore-test` von Hand). Er spielt die letzte Sicherung in einen Wegwerf-Container ein und prüft sie. Das Ergebnis steht im Server-Panel.
- **Überwachung (Watchdog)**: Alle 5 Minuten werden Container, Portal, Speicherplatz und Sicherungen geprüft. Alarme kommen per E-Mail, optional zusätzlich per Telegram (`mkctl alarm-telegram <Bot-Token> <Chat-ID>`).
- **Ausfall von außen**: Der Watchdog läuft auf demselben Server. Für den Fall, dass der ganze Server aus ist, zusätzlich einen kostenlosen externen Dienst wie UptimeRobot auf `https://portal.markentrix.de/healthz` einrichten.
- **Testsystem**: siehe `docs/TESTSYSTEM.md`.

## Server-Härtung (wird bei der Installation eingerichtet)

- **Automatische Sicherheitsupdates** des Betriebssystems (unattended-upgrades). Braucht ein Update einen Neustart, meldet der Watchdog das erst nach 7 Tagen per E-Mail; dann `reboot` in der Hetzner-Konsole.
- **fail2ban** sperrt IPs nach 5 falschen SSH-Anmeldungen für 1 Stunde.
- **Log-Rotation**: Docker-Logs sind auf 3 × 10 MB je Container begrenzt, damit die Platte nicht vollläuft.
- **n8n-Version festgehalten**: Die Installation merkt sich die laufende n8n-Version in `.env` (`N8N_VERSION`). Ein `mkctl update` springt dadurch nicht ungewollt auf eine neue Hauptversion. Gezielt wechseln: `mkctl n8n-version <Version>`; vorher wird eine Sicherung gemacht.
- **SSH nur mit Schlüssel**: Erst sicherstellen, dass ein eigener Schlüssel in `/root/.ssh/authorized_keys` steht und du dich damit anmelden kannst (zweites Fenster offen lassen!). Dann `mkctl ssh-haerten`. Rückgängig: `mkctl ssh-haerten --rueckgaengig`. Die Hetzner-Web-Konsole funktioniert unabhängig davon immer weiter.
- **Hetzner Cloud Firewall** (im Hetzner-Konto, nicht auf dem Server): nur Ports 22, 80 und 443 eingehend erlauben.

## Zahlungseingänge abgleichen

Unter „Angebote & Rechnungen" ganz oben: Kontoauszug als CSV aus dem Online-Banking exportieren, Datei auswählen, „Vorschau". Das Portal sucht in den Verwendungszwecken nach Rechnungsnummern offener Rechnungen.

- **Passt genau** (Nummer und Betrag stimmen): kann mit einem Klick als bezahlt gebucht werden.
- **Betrag weicht ab** (Teilzahlung, Skonto, Überzahlung): wird nie automatisch gebucht, bitte selbst prüfen.
- **Nicht zugeordnet**: nur zur Info. Ausgänge werden ignoriert.

Erst die Vorschau, dann „buchen". Derselbe Auszug kann gefahrlos zweimal hochgeladen werden.

## Kunde beendet den Vertrag (Offboarding)

Im Kunden, wenn der Status „gekündigt" oder „beendet" ist, gibt es die Karte „Vertragsende: Datenexport und Löschung":

1. **Datenexport (ZIP)**: alle Daten des Kunden (Anfragen, Kontakte, Wissensbasis, Chat, Rechnungen als PDF, Berichte, AVV, hochgeladene Dateien) zum Übergeben an den Kunden. Passwörter sind nicht enthalten.
2. **Löschen**: Haken „Export wurde übergeben" setzen und die Kundennummer eintippen. Gelöscht werden Inhalte, Zugänge, Kontaktdaten und die Website-Dateien (Website-Ordner erst nach 14 Tagen endgültig, Papierkorb). **Bleiben müssen** aus gesetzlichen Gründen Stammdaten, Rechnungen/Angebote, Verträge, Buchungen, Provisionen, AVV und das Protokoll. Das Löschprotokoll hält fest, was wann gelöscht wurde. Aufbewahrungsfristen (i. d. R. 6 bzw. 8 bis 10 Jahre) bitte mit der Steuerberatung bestätigen.

## Fehler im Portal

Unerwartete Fehler zeigen dem Nutzer nur „Interner Fehler" und erscheinen als Warnung in der Übersicht (unter Alarme), höchstens einmal je Seite und 10 Minuten. Dort bestätigen, wenn erledigt.

## Zusammenarbeit mit Kunden (Nachrichten, Freigaben, Aufgaben, Dokumente)

**Nachrichten (Admin → Nachrichten):** Kunden schreiben im Portal unter „Nachrichten“ (Frage, Auftrag, Änderungswunsch, Problem). Du bekommst eine E-Mail und einen roten Zähler. Antwort mit „Senden“; Status setzen (offen, in Arbeit, wartet auf Kunde, erledigt). „Nur intern“ ist eine Notiz, die der Kunde nie sieht. Bei „erledigt“ wird der Kunde um eine Bewertung (0 bis 10) gebeten. Du kannst auch selbst eine Nachricht oder einen Auftrag an einen Kunden schicken (Kunde öffnen → Nachrichten → Neue Nachricht).

**Freigaben (Kunde öffnen → Neue Freigabe-Bitte):** Text, Beitrag oder Entwurf (optional mit Datei) zur Prüfung schicken. Der Kunde gibt frei oder wünscht eine Änderung (Kommentar Pflicht). Datum, Uhrzeit, Name und IP werden gespeichert. Übersicht aller Freigaben: Admin → Freigaben.

**Aufgaben (Admin → Aufgaben):** Eigene To-dos mit Zuständigem und Fälligkeit. Das System legt selbst Aufgaben an (unbeantwortete Nachrichten, wartende Freigaben) und schickt täglich eine Zusammenfassung. Automatische Aufgaben nur „Erledigt“ markieren.

**Kennzahlen (Admin → Kennzahlen):** Antwortzeit, Bearbeitungsdauer, Freigabedauer, Zufriedenheit und NPS der letzten 90 Tage, dazu eine Tabelle pro Kunde. Kunden sehen auf ihrer Übersicht die eigenen Zahlen und werden einmal pro Quartal um eine Bewertung gebeten.

**Dokumente (Kunde öffnen → Dokumente):** Verträge, Briefings, Logos pro Kunde ablegen, mit Schalter „für Kunden sichtbar“. Kunden haben unter „Dokumente“ ihre eigene Ablage. Erlaubt: PDF, Bilder, Word, Excel, PowerPoint, Text, CSV, ZIP bis 8 MB. Passwörter gehören nicht hierher.

**Selbstbedienung:** Kunden (Inhaber) ändern ihre Rechnungsanschrift selbst, fragen Zusatzmodule per Knopf „Anfragen“ an (landet als Nachricht bei dir) und schalten E-Mails zu Antworten ein oder aus. Firmenname und Rechtsform änderst du.

Beim Beenden eines Kunden (Offboarding) sind Nachrichten, Freigaben, Bewertungen und Dokumente im Datenexport enthalten und werden danach gelöscht.

**Briefing:** Neue Kunden sehen im Portal einen Hinweis und das Menü „Briefing“ (Fragebogen zu Unternehmen, Öffnungszeiten, Auftritt, Inhalten, Zielen). Sie können zwischenspeichern und später abschicken. Beim Abschicken bekommst du eine E-Mail und eine Aufgabe. Die Antworten stehen beim Kunden unter „Briefing“.

**Auswertung:** Kunden sehen unter „Auswertung“ Anfragen, Termine, Anrufe und Agent-Aktionen im laufenden Monat mit Vergleich zum Vormonat, den Verlauf über 12 Wochen, die Quellen der Anfragen und, wenn du sie einträgst, Besucher und Google-Zahlen. Letztere trägst du beim Kunden unter „Zahlen für die Auswertung“ monatlich ein (Besucher, Google-Aufrufe, Bewertungen, Sterne). Sie kommen nicht automatisch.

**Hilfe:** Kunden finden im Menü „Hilfe“ Antworten auf häufige Fragen mit Suche. Funktionen, die ein Kunde nicht gebucht hat, werden ausgeblendet. Die Texte stehen in `portal/static/js/kunde.js` (Liste `HILFE`).

**Website-Check → Leads:** Wer den Check auf markentrix.de nutzt, erscheint als Lead (Admin → Leads) mit Ergebnis und Mail ans Team. Einrichtung: `docs/WEBSITE-CHECK.md`.

## Leads, Onboarding und AVV (Stand Oktober 2026)

- **Übersicht „Heute zu tun“**: oben auf der Admin-Übersicht stehen Nachrichten ohne Antwort, fällige Aufgaben, neue Leads, wartende Freigaben, hängende Onboardings, überfällige Rechnungen und fehlende AVV.
- **Leads**: Einstufung Cold / Warm / HOT (Auswahl in Liste und Detail), Löschen-Knopf, „Angebot erstellen“ (legt bei Bedarf den Kunden an). Leads aus dem Website-Check starten als „Warm“, Anfragen über das Kontaktformular als „HOT“. Schlüssel und Einrichtung: `docs/WEBSITE-CHECK.md`, Schlüssel ablegen mit `bash bin/lead-key.sh`.
- **Onboarding**: Der Kunde sieht auf seiner Übersicht „Dein Start“ mit Fortschritt und den Schritten, bei denen er etwas tun muss. Nach 3 Tagen bekommt er einmal pro Woche eine Erinnerung per Mail, nach 5 Tagen entsteht für dich eine Aufgabe „Onboarding nachfassen“. In der Kundenliste steht bei Kunden im Onboarding „Start: x von y“.
- **Module** sind in der Kundenliste einzeln sichtbar und dort schaltbar.
- **AVV per Klick**: Kunde → AVV → „Im Portal zur Bestätigung freigeben“. Der Kunde bekommt eine Mail, liest den Vertrag und bestätigt mit Namen und Häkchen. Das PDF enthält danach einen Bestätigungsvermerk (Name, Zeit, Prüfsumme), der Nachweis liegt zusätzlich in der Datenbank. Der Weg über Mail und Upload eines unterschriebenen PDFs bleibt möglich.
- **Unterauftragsverarbeiter im AVV**: Einstellungen → „AVV: Unterauftragsverarbeiter“. Leer lassen = Standardliste.

## Weitere Funktionen (Oktober 2026)

- **Kontaktergebnis** bei Leads (Admin und Vertriebler): per Klick „Angerufen: erreicht / nicht erreicht", „E-Mail geschickt", „Termin vereinbart" usw. Status und Wiedervorlage ziehen automatisch nach, der Verlauf wird geführt.
- **Monatsbericht**: unter dem Kunden „Texte" öffnen, Einordnung und nächste Schritte schreiben (oder KI-Entwurf), speichern, erneut senden. Beides steht im PDF und im Kundenportal.
- **Status-Seite** im Kundenportal: offene Anfragen, was auf den Kunden wartet, Erreichbarkeit der Websites, aktive Module.
- **Folgemails** (Einstellungen → Folgemails): standardmäßig aus. Nur Leads mit Einwilligung, mit Abmeldelink. Vor dem Einschalten rechtlich prüfen lassen.
- **Terminbuchung** (Einstellungen → Terminbuchung): Seite `/buchen` im Portal, Link auf die Website setzen. Interessenten wählen einen Slot, du bekommst Mail mit Kalendereinladung, der Lead steht auf „Termin".
- **Mitarbeiter & Rechte** (Einstellungen): Mitarbeiter einladen und nur Bereiche freigeben (Kunden, Nachrichten, Leads, Rechnungen & Preise, Einstellungen). Nur Konten mit vollem Zugriff verwalten das.
- **Leads aus Excel/CSV importieren** (Leads, weiter unten): Datei wählen, mit „Datei prüfen“ die Vorschau ansehen (erkannte Spalten, Dubletten, Fehler), dann importieren. Listenname, Einstufung und Vertriebler legst du gleich fest. Die Leadliste hat Filter für Suche, Quelle, Einstufung, Vertriebler und Importliste.
- **Leads-Übersicht**: 50 Leads pro Seite, Haken vorne für Sammelaktionen (Einstufung, Vertriebler, Status setzen, löschen), auch für alle Treffer eines Filters.
- **Vertriebler einladen**: Beim Anlegen (Haken „Einladung senden“) oder später in der Vertriebsliste über „Einladung senden“. Der Vertriebler bekommt eine Mail mit Link zum Passwort setzen für das Vertriebsportal.
- **Vertriebler: „Heute anrufen“** ist die Startseite des Vertriebsportals: fällige Wiedervorlagen, heiße Leads ohne Anruf, neu zugewiesene Leads, mit Telefon-Button.
- **Gesprächsleitfaden (KI)** in jedem Lead (Admin und Vertrieb): Einstieg, Fragen, Nutzen, drei Einwände mit Antworten, Abschluss. Braucht den KI-Schlüssel (Einstellungen → KI). Nur ein Vorschlag, nichts ablesen oder versprechen.
- **Vertriebs-Auswertung** (Admin, links): Trichter von Leads über Bearbeitet, Erreicht, Termine bis Kunden, je Vertriebler, Importliste, Branche und Quelle.
- **Systemstatus** oben in der Admin-Übersicht: Sicherung, externe Sicherung, Festplatte, Zertifikat, E-Mail-Versand. Die Daten liefert die Server-Überwachung (watchdog), nach dem Update ab dem nächsten 5-Minuten-Lauf. Meldet sie sich länger als eine Stunde nicht, kommt eine Mail.
- **Anmelde-Link per E-Mail** auf der Login-Seite für Kunden und Vertriebler ohne Zwei-Faktor-Anmeldung (15 Minuten gültig, einmalig). Administratoren und Konten mit 2FA melden sich weiter mit Passwort.
- **Änderungshistorie** bei jedem Kunden: wer hat wann was geändert.
- **Kunden-Frühwarnung** (oben in der Admin-Übersicht): Kunden mit Anzeichen für eine Kündigung (lange nicht angemeldet, Anfragen eingebrochen, überfällige Rechnung, schlechte Zufriedenheit, unbeantwortete Nachricht). Jeden Montag kommt dazu eine Mail.
- **Lastschrift oder Überweisung**: Einstellungen → „Zahlung & Mahnwesen“: Gläubiger-ID (kostenlos bei der Bundesbank) eintragen, IBAN in den Firmendaten. Danach kann der Kunde unter Angebote & Rechnungen ein SEPA-Mandat erteilen (Bestätigungsmail inklusive). Unter Angebote & Rechnungen → „Lastschrift-Einzug“ wählst du Rechnungen und das Einzugsdatum, das Portal erstellt die Datei (pain.008) für das Online-Banking und kündigt den Einzug per Mail an. Den Zahlungseingang bucht wie bisher der Kontoauszug-Abgleich. Bei Rücklastschrift: „Zurücksetzen“. Es gibt kein Zahlungsdienst-Konto und keine Online-Kartenzahlung.
- **Automatische Zahlungserinnerungen** (gleiche Einstellung, standardmäßig aus): Erinnerung, 1. und 2. Mahnung nach einstellbaren Tagen, werktags, nicht bei angekündigtem Einzug und nicht bei Referenzkunden. Keine Gebühren oder Zinsen.
- **Anrufprotokoll** (Einstellungen → Telefon-Assistent): Geheimnis erzeugen, beim Anbieter des Telefon-Assistenten (z. B. Famulor) einen Webhook auf `/api/webhook/telefon/KUNDENNUMMER?s=GEHEIMNIS` eintragen. Anrufe erscheinen beim Kunden unter „Anrufe“, eingehende zusätzlich als Anfrage. Nummern, Namen und Zusammenfassungen werden nach 180 Tagen gelöscht. Das genaue Format des Anbieters wird tolerant gelesen, bitte mit einem Testanruf prüfen.
- **Branchenvorlagen**: beim Kunden unten „Branchenvorlage“ (Kfz, Friseur, Restaurant, Handwerk, Einzelhandel, Fitness): legt Wissenseinträge (inaktiv, mit Platzhaltern), Beitrags-Entwürfe und Aufgaben an. Nichts wird veröffentlicht oder vom Assistenten benutzt, bevor du es prüfst und aktivierst.
- **App & Push-Nachrichten**: in Einstellungen (Admin), Konto (Vertrieb) und Einstellungen (Kunde) gibt es die Karte „App & Benachrichtigungen“. Anlässe: neue Anfrage/Anruf (Kunde), neue Leads und „Heute anrufen“ am Morgen (Vertrieb), Gespräch gebucht, Kundennachricht, Website-Check, Frühwarnung (Admin). Die Nachrichten enthalten keine Namen. Auf dem iPhone geht es erst, wenn das Portal zum Home-Bildschirm hinzugefügt wurde.
- **Suche (Strg+K)**: im Admin-Menü oben „Suchen“ – findet Kunden, Leads, Rechnungen/Angebote, Nachrichten und Aufgaben (nur in den Bereichen, für die dein Konto Rechte hat).
- **Zustand & Verlauf**: auf jeder Kundenseite ganz oben – Risiko, offene Beträge, letzter Login, nächste Aufgabe und eine Zeitachse aller Ereignisse.
- **Geschäftszahlen**: auf der Admin-Übersicht (MRR, Kündigungen, offene Rechnungen, Zahlungseingang 12 Monate). Am Monatsanfang kommt eine Zusammenfassung per Mail.
- **Ansicht anpassen**: Button oben rechts auf der Übersicht (Admin und Kunde) – nicht benötigte Karten ausblenden. Gilt pro Person.
- **Glocke 🔔**: in allen drei Portalen; sammelt die Benachrichtigungen, auch ohne Push. Welche Anlässe als Push kommen, stellst du in der Karte „App & Benachrichtigungen“ ein.

## Automatische Tests

`sudo bash tests/run.sh` auf einem Entwicklungsrechner (nie auf dem Produktivserver) legt eine eigene Test-Datenbank an und prüft alle Funktionen. Bei GitHub läuft derselbe Test bei jedem Push (Reiter „Actions").
