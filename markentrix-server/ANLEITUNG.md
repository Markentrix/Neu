# Markentrix Server-Paket: Anleitung

Dieses Paket richtet auf deinem Hetzner-Server alles Neue mit **einem Befehl** ein:

- **PostgreSQL-Datenbank** mit fertiger Struktur (66 Tabellen): Kunden mit Kundennummer, Zugänge, Preiskatalog (Preisliste Stand September 2026) und Buchungen, Kundenbereich, Konfiguration und Prompts, Wissensbasis und Agentenläufe, Vertrieb, Akquise und Lead-Finder, Kommunikation, Datenschutz (Einwilligungen, Auskunft, Löschung) und Qualität (Befunde, Maßnahmen, Ausnahmeregister, Alarme). Jeder Kunde sieht nur seine eigenen Daten (getestet). Kein Supabase.
- **n8n** (deine Workflows), mit eigener Datenbank
- **Server-Dashboard** unter `panel.deine-domain.de` (nur lesend): zeigt Dienste, Websites, Demos, Speicher und Sicherungen
- **Tägliche Sicherung** um 03:15 Uhr, 30 Tage Aufbewahrung (laut AVV)
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
1. „Neuen AVV erstellen“: im Dialog die **gebuchten Module ankreuzen** (E-Mail und Terminbuchung: über dein Konto oder das des Kunden), Domain bzw. „Sonstiges“ eintragen, Datum des Hauptvertrags und die weisungsberechtigte Person angeben. Daraus entstehen Anlage 1 (angekreuzte Module) und Anlage 3 (nur die dazugehörigen Unterauftragsverarbeiter). Der Vertragstext ist **Version 2** (Vorlage `Markentrix_AVV_Version_2_Vorlage.docx`, mit Anlage 2 zu den technischen Maßnahmen). Dann **Vertrag (PDF)** öffnen. Fehlt noch etwas (z. B. das Datum), sperrt das Portal Mailversand und Freigabe und zeigt unter „Module & Angaben prüfen“, was fehlt. Bereits bestätigte oder abgelegte AVV (Version 1) bleiben unverändert erhalten.
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
- **Anrufprotokoll** (Einstellungen → Telefon-Assistent): Geheimnis erzeugen, beim Anbieter des Telefon-Assistenten (z. B. Famulor) einen Webhook auf `/api/webhook/telefon/KUNDENNUMMER?s=GEHEIMNIS` eintragen. Anrufe erscheinen beim Kunden unter „Anrufe“, eingehende zusätzlich als Anfrage. Nummern, Namen und Zusammenfassungen werden nach 180 Tagen gelöscht. Das genaue Format des Anbieters wird tolerant gelesen, bitte mit einem Testanruf prüfen. **Besser:** Je Kunde eine eigene Adresse (dort „Adresse zeigen“ mit der Kundennummer): Das Geheimnis gilt nur für diesen Kunden. Sind alle Anbieter umgestellt, „Gemeinsames Geheimnis abschalten“ aktivieren. Ein neues Hauptgeheimnis macht alle Adressen ungültig.
- **Branchenvorlagen**: beim Kunden unten „Branchenvorlage“ (Kfz, Friseur, Restaurant, Handwerk, Einzelhandel, Fitness): legt Wissenseinträge (inaktiv, mit Platzhaltern), Beitrags-Entwürfe und Aufgaben an. Nichts wird veröffentlicht oder vom Assistenten benutzt, bevor du es prüfst und aktivierst.
- **App & Push-Nachrichten**: in Einstellungen (Admin), Konto (Vertrieb) und Einstellungen (Kunde) gibt es die Karte „App & Benachrichtigungen“. Anlässe: neue Anfrage/Anruf (Kunde), neue Leads und „Heute anrufen“ am Morgen (Vertrieb), Gespräch gebucht, Kundennachricht, Website-Check, Frühwarnung (Admin). Die Nachrichten enthalten keine Namen. Auf dem iPhone geht es erst, wenn das Portal zum Home-Bildschirm hinzugefügt wurde.
- **Befehlspalette (Strg+K)**: im Admin-Menü oben „Suchen“ – findet Kunden, Leads, Rechnungen/Angebote, Nachrichten und Aufgaben und bietet Aktionen an (z. B. „Neuer Kunde“, „Rechnung für …“). Der Knopf **+ Neu** darunter zeigt nur die Anlegen-Aktionen. Alles nur für Bereiche, für die dein Konto Rechte hat.
- **Zustand & Verlauf**: auf jeder Kundenseite ganz oben – Risiko, offene Beträge, letzter Login, nächste Aufgabe und eine Zeitachse aller Ereignisse.
- **Jetzt wichtig**: erste Karte der Admin-Übersicht – eine Liste, nach Dringlichkeit sortiert (Systemprobleme, überfällige Rechnungen, Kündigungsrisiko, Nachrichten, Aufgaben …). Bereiche ohne Handlungsbedarf erscheinen nur als grüne Markierung. Die älteren Einzelkarten (System, Heute, Frühwarnung) sind standardmäßig ausgeblendet; über „Ansicht anpassen“ kannst du sie wieder einblenden.
- **Geschäftszahlen**: auf der Admin-Übersicht (MRR, Kündigungen, offene Rechnungen, Zahlungseingang 12 Monate) mit Vergleich zum Vormonat, anklickbaren Kacheln, **MRR-Ziel** (Button „MRR-Ziel setzen“), Verkaufstrichter der letzten 90 Tage und einer 30-Tage-Prognose der erwarteten Zahlungseingänge. Vergleiche und Trichter werden erst mit Daten aussagekräftig. Am Monatsanfang kommt eine Zusammenfassung per Mail.
- **Dein Monat mit Markentrix** (Kunden-Übersicht): Anfragen, Anrufe und Termine dieses Monats im Vergleich zum Vormonat, „Dein nächster Schritt“ und ein Knopf „Zusammenfassung kopieren“.
- **Ansicht anpassen**: Button oben rechts auf der Übersicht (Admin und Kunde) – nicht benötigte Karten ausblenden. Gilt pro Person.
- **Zahlungserinnerung mit Klick**: In „Jetzt wichtig“, auf „Mein Tag“ und in der Rechnungsliste („Zahlungserinnerungen prüfen“, auch über Strg+K) öffnet sich ein Fenster mit allen überfälligen Rechnungen, der nächsten Stufe (Erinnerung, 1. Mahnung, 2. Mahnung) und einem fertigen Mailtext. Du kannst jeden Text ansehen und ändern und sendest dann die ausgewählten Mails (mit PDF). Es wird nichts automatisch verschickt. Warnung, wenn gerade erst gemahnt wurde. Das automatische Mahnwesen bleibt davon unabhängig und bis zur Rechtsprüfung aus.
- **Sammelaktionen**: In Kundenliste und Rechnungsliste Haken setzen. Kunden: Aufgabe für alle anlegen, Sammelmail (mit Vorlage und Platzhaltern, höchstens 40, jeder bekommt seine eigene Mail), Aufgabenpaket, CSV. Rechnungen: Erinnerungen dazu prüfen, CSV. Leads hatten das schon.
- **Gespeicherte Filter**: In Kunden (Suche, Status, AVV fehlt, Referenz), Leads und Rechnungen: Filter setzen, „Aktuelle Auswahl speichern“. Danach im Auswahlfeld oder unter „Mein Tag → Meine Filter“ mit einem Klick öffnen. „Link kopieren“ gibt eine Adresse, die den Filter enthält.
- **Mein Tag**: Eigene Seite im Menü: deine fälligen Aufgaben (mit „Erledigt“), Wiedervorlagen, wartende Nachrichten, überfällige Rechnungen, hängende Freigaben, fehlende AVV und deine gespeicherten Filter.
- **Textvorlagen** (Einstellungen): Mail-Vorlagen (Willkommen, Rückfrage zum Briefing, Terminbestätigung, Freigabe-Erinnerung) mit Platzhaltern {firma}, {name}, {kundennummer}, {ort}. Sie lassen sich in Nachrichten-Antworten einfügen und in Sammelmails nutzen. Aufgabenpakete (z. B. „Neuer Kunde: 8 Schritte“) legst du beim Kunden mit „Aufgabenpaket anlegen“ an; doppelt anlegen erzeugt nichts doppelt.
- **Betriebs-Ampel** (Übersicht): Server-Überwachung, lokale und externe Sicherung, Zertifikat, Speicherplatz, Hintergrundjobs und Mailversand als Ampel. Rot erscheint auch in „Jetzt wichtig“. Grau heißt: noch keine Messwerte (z. B. Wächter noch nicht eingerichtet).
- **Betriebsalarm**: Wird ein Punkt der Betriebs-Ampel rot (Sicherung, Zertifikat, Speicher, Mailversand, stumme Überwachung), bekommen alle Admins sofort eine Push-Nachricht (auch in der Glocke) und eine Mail. Bleibt es rot, kommt nach 24 Stunden eine Erinnerung; wird es wieder grün, eine Entwarnung. Abschalten unter „App & Benachrichtigungen“ → „Betriebsalarm“.
- **Glocke 🔔**: in allen drei Portalen; sammelt die Benachrichtigungen, auch ohne Push. Welche Anlässe als Push kommen, stellst du in der Karte „App & Benachrichtigungen“ ein.

## Automatische Tests

Weitere Unterlagen: `docs/ARCHITEKTUR.md` (Aufbau für Entwickler), `docs/LOESCHKONZEPT.md`, `docs/PILOT-CHECKLISTE.md`. Beispieldaten zum Üben: `mkctl demo-daten` (wieder löschen: `mkctl demo-daten-entfernen`).

`sudo bash tests/run.sh` auf einem Entwicklungsrechner (nie auf dem Produktivserver) legt eine eigene Test-Datenbank an und prüft alle Funktionen. Bei GitHub läuft derselbe Test bei jedem Push (Reiter „Actions").

## Vertriebler-Portal: Mein Tag, Leitfaden, Zahlen, Angebotsanfrage

- **Heute anrufen** (Startseite, handytauglich): oben der Wochenfortschritt, darunter fällige Wiedervorlagen, heiße und neue Leads. Pro Lead: *Anrufen* (Telefon wählt), *Nicht erreicht* (ein Klick, Wiedervorlage in 2 Tagen), *Gesprochen …* und *Termin …* (Dialog mit Notiz und Wiedervorlage mit Schnellwahl Morgen / In 3 Tagen / Nächste Woche), *Kein Interesse* (mit Rückfrage). Erledigte Leads verschwinden aus der Liste.
- **Lead-Detail**: „Kontakt festhalten“ mit Schnellwahl und „Speichern & nächster Lead“; Branchenhinweis (wenn die Branche erkannt wird); „Angebot anfragen“; „Nach dem Gespräch“ (Mail-Entwurf, öffnet das eigene Mailprogramm, das Portal verschickt nichts).
- **Leitfaden**: Eröffnung, Fragen, Einwände, Abschluss und Branchenhinweise. Admin: *Einstellungen → Gesprächsleitfaden* (Textformat, „Auf Standard zurücksetzen“). Es sind Vorschläge ohne Preise und Zusagen; Formulierungen bitte rechtlich prüfen lassen.
- **Meine Zahlen**: Anrufe, erreicht, Termine, neue Kunden (Woche/Monat, Vergleich zur Vorwoche), Quoten, Wochenziel (änderbar) und ein *Rechenbeispiel* zur Provision. Das Beispiel ist keine Zusage.
- **Angebotsanfragen**: Der Vertriebler wählt Paket und Notiz. Du erhältst eine Aufgabe und eine Mitteilung, im Lead (Admin) setzt du den Status (Angefragt / In Prüfung / Angebot ist raus / Angenommen / Abgelehnt) und einen Hinweis; der Vertriebler wird benachrichtigt.

## Kunden-Portal: Heute, Anfragen-Inbox, Bewertungen

- **Heute** ist die Startseite der Kunden (handytauglich): offene Anfragen und Rückrufe (Anrufen, Antworten, Erledigt, Spam), Termine heute und morgen (Bestätigen, Erledigt, Nicht erschienen, Absagen), was auf ihn wartet (Freigaben, Nachrichten) und Bewertungsvorschläge.
- **Antworten** (auch in der Anfragen-Liste): fünf Standardvorlagen (Termin bestätigen, Rückruf, Wir melden uns, Rückfrage, Absage) plus eigene Vorlagen; Platzhalter {name} und {firma} werden gefüllt. Das Portal verschickt nichts: Der Kunde öffnet damit sein eigenes Mailprogramm, WhatsApp oder SMS; danach wird die Anfrage als beantwortet markiert.
- **Bewertungen** (Modul Anfragen & Termine): Der Kunde hinterlegt seinen Google-Bewertungslink, bereitet Bitten vor (Vorschläge aus erledigten Terminen der letzten 30 Tage, oder manuell), prüft den Text und sendet selbst. Dieselbe Person wird innerhalb von 90 Tagen nur einmal gefragt. Hinweise zu Freiwilligkeit und Werbung per Mail stehen auf der Seite; bitte rechtlich prüfen lassen (docs/ANWALT-CHECKLISTE).
- **Admin-Übersicht**: Einträge unter „Jetzt wichtig“ lassen sich pro Browser 7 Tage ausblenden („Wieder anzeigen“ holt sie zurück). Die Ursache bleibt bestehen, nur der Hinweis wird ruhiggestellt.

## Diagramme, Reise-Karte, Onboarding-Board, Pipeline, Suche, Rückgängig

- **Kunden → Auswertung → „Dein Verlauf“**: Anfragen und Termine pro Woche (26 volle Wochen), Quellen-Ring, Trichter Anfrage → Termin, Anfragen nach Wochentag, Antwortzeit (ab 2 Monaten Daten) und Klartext-Sätze. Bei weniger als 10 Anfragen in 90 Tagen steht ehrlich, dass es noch keine Aussage gibt. Jedes Diagramm hat eine Tabelle als Alternative; „Drucken / als PDF speichern“ nutzt die Druckfunktion des Browsers.
- **Reise-Karte** (Kunden-Übersicht, solange der Kunde im Onboarding ist): Phasen Start, Briefing & Material, Aufbau, Live & Übergabe mit Haken; darunter nur die Schritte der aktuellen Phase.
- **Admin → Onboarding**: Spalten pro Phase. Die Phase ergibt sich automatisch aus der Checkliste (erste Phase mit offenem Punkt), Karten werden deshalb nicht von Hand gezogen. „Hängt am Start“ erscheint nach 5 Tagen ohne erledigte Startpunkte.
- **Admin → Pipeline** und **Vertriebler → Pipeline**: Leads als Spalten (Neu bis Gewonnen), Verschieben per Ziehen oder Auswahlfeld, danach 10 Sekunden „Rückgängig“. Pro Spalte werden 25 Leads gezeigt (heiß zuerst), der Rest steht in der Liste. Trichter mit Abschlussquote der letzten 180 Tage (erst ab 8 entschiedenen Leads). Die **Prognose** (nur Admin) rechnet: offene Angebote × Abschlussquote × durchschnittlicher Monatswert je Kunde. Das ist eine Schätzung, keine Zusage.
- **Suche (Strg+K)** findet zusätzlich Kundenanfragen, Termine und Vertriebler und zeigt ohne Eingabe die zuletzt geöffneten Seiten (nur in diesem Browser).
- **Rückgängig** gibt es bei Sammelaktionen (Aufgaben, Aufgabenpakete; erledigte bleiben erhalten), „Ausblenden“ in der Übersicht, Pipeline-Verschiebungen und bei Anfragen/Terminen auf der Kunden-Seite „Heute“. Versendete Sammelmails lassen sich nicht zurückholen.

## Menü, „Heute zuerst“ und Darstellung
- **Menü in Gruppen** (Admin, Kunden-Portal, Vertriebler-Portal): Die Punkte sind nach Arbeitsablauf sortiert, zum Beispiel „Täglich“, „Verstehen“, „Mein Betrieb“, „Verwaltung“. Ein Klick auf den Gruppennamen klappt sie auf oder zu; das merkt sich das Gerät. Die Gruppe der gerade geöffneten Seite ist immer offen. Ist eine Gruppe zu, zeigt sie die Zahl der offenen Hinweise. Auf dem Handy bleibt das Menü eine durchgehende Leiste.
- **Admin „Heute zuerst“**: Oben auf der Übersicht stehen die 3 wichtigsten Dinge des Tages mit einem Knopf. Die Reihenfolge kommt aus derselben Liste wie „Jetzt wichtig“; ausgeblendete Hinweise erscheinen auch hier nicht. Die Karte lässt sich über „Ansicht anpassen“ ausblenden.
- **Kunden „Dein nächster Schritt“**: Auf „Heute“ steht genau ein Schritt, zum Beispiel die älteste Anfrage beantworten, einen Termin bestätigen oder eine Freigabe prüfen. Ist nichts offen, steht dort „Alles erledigt“.
- **Wochenrückblick**: Montags ab 8 Uhr bekommen Kunden, Vertriebler und Admins eine Push-Nachricht mit den Zahlen der letzten Woche (nur Zahlen, keine Namen). Abschaltbar unter „App & Benachrichtigungen“ → „Montags: Wochenrückblick“.
- **Dunkelmodus**: Der Knopf neben der Glocke wechselt zwischen automatisch (folgt dem Gerät), hell und dunkel. Die Wahl wird je Gerät gemerkt.

## Angebot direkt an einen Lead senden
- Im Lead oben auf **„Angebot senden“**. Im Dialog Paket aus dem Katalog wählen (Preise kommen aus „Preise & Konditionen“, du kannst sie anpassen), bei Bedarf eigene Positionen ergänzen, Empfänger-Mail prüfen, **„PDF-Vorschau“** ansehen und **„Angebot jetzt senden“**. Der Lead wird dafür nicht zum Kunden.
- Der Lead bekommt eine Mail mit dem PDF und einem **Online-Link**. Auf der Seite sieht er das Angebot, öffnet das PDF und kann mit Namen und einem Klick **verbindlich annehmen** oder ablehnen. Der Link ist geheim, nur für dieses Angebot und bei erneutem Senden wird ein neuer erzeugt (der alte erlischt).
- Du bekommst Push, Glocke und bei Annahme eine Mail: **angesehen**, **angenommen**, **abgelehnt**. Bei Annahme legt das Portal eine Aufgabe „Kunde anlegen“ an. Dann im Lead **„Zum Kunden machen“**: Das Angebot wandert mit zum Kunden, daraus lässt sich die Rechnung erstellen.
- Ist der E-Mail-Versand nicht eingerichtet, bekommst du den Link zum Kopieren (für WhatsApp oder dein Mailprogramm).
- Der Vertriebler sieht den Stand seiner Angebotsanfrage automatisch („Angebot ist raus“, „angenommen“). Gesperrte Leads, Leads ohne Einwilligung, verlorene und tote Leads bekommen kein Angebot. Wird ein Lead gelöscht, verschwinden auch seine Angebote.
- **Nummer falsch / nicht erreichbar** im Lead legt ihn ab (Status „tot“, keine Wiedervorlage mehr).

## Handy-Leiste, Erststart-Tour und Nutzungsmessung

- **Handy-Leiste (Kunden):** Am Handy gibt es unten eine feste Leiste mit „Heute“, „Anfragen“, „Termine“ und „Mehr“. „Mehr“ öffnet das ganze Menü samt Dunkelmodus und Abmelden. Buttons und Eingabefelder sind größer, damit man sie mit dem Daumen trifft. Ein Wischen zwischen Seiten gibt es bewusst nicht.
- **Erststart-Tour:** Beim ersten Login zeigt das Kunden-Portal drei kurze Schritte (Heute, Anfragen/Nachrichten, Hilfe). „Überspringen“ oder „Fertig“ merkt sich das Konto. Unter „Hilfe“ gibt es „Tour nochmal ansehen“.
- **Nutzungsmessung:** Unter Admin → Protokoll steht, welche Seiten genutzt werden, wie viele Personen in den letzten 7/30 Tagen aktiv waren und wie viele Kunden die Tour gesehen haben. Gespeichert werden nur Seitenname, Tag und Rolle (keine Inhalte), nach 180 Tagen wird gelöscht. Der Satz steht in der Standard-Datenschutzerklärung; falls ihr einen eigenen Text habt, bitte ergänzen.

## Angebot an Neukunden

Unter Admin → Angebote & Rechnungen gibt es oben „+ Angebot an Neukunden“. Du trägst nur Firma und E-Mail ein (Ansprechpartner, Telefon, Ort sind optional), der Kontakt wird als Lead angelegt und es öffnet sich direkt der Angebotsdialog. Das PDF kommt im Markentrix-Design (Navy-Kopf, Farbverlauf, Inter/Space Grotesk), der Kunde bekommt Mail mit PDF und Link und kann online annehmen oder ablehnen. Nach der Annahme legst du ihn mit „Zum Kunden machen“ an, das Angebot wandert mit.

Im Angebotsdialog steht unter den Positionen **„Das bekommt der Kunde“**. Der Text kommt aus dem gewählten Paket (Leistungsumfang je Produkt) und lässt sich pro Angebot frei ändern: eine Zeile pro Punkt, „## “ davor macht eine Zwischenüberschrift. Er erscheint im PDF als Karte „Das bekommen Sie“ mit Häkchen und auf der Online-Angebotsseite. Die Standardtexte der Pakete (außer BUSINESS WEB) sind aus der Katalogbeschreibung abgeleitet, bitte einmal prüfen.

**Angebote im Blick:** Auf der Admin-Übersicht zeigt die Karte „Angebote im Blick“ alle offenen Angebote (an Leads und Kunden) mit Stand: *Angenommen*, *Angesehen* (der Kunde hat den Link geöffnet, aber noch nicht geantwortet), *Gesendet, noch nicht geöffnet*, *Abgelaufen*, *Abgelehnt*. Angenommene und abgelehnte bleiben 30 Tage sichtbar. Dazu melden sich „Heute zuerst“ und „Jetzt wichtig“: angenommen → Kunde anlegen, angesehen → jetzt anrufen, seit 3 Tagen ungeöffnet → nachfassen. Die Karte lässt sich unter „Ansicht anpassen“ aus- und einblenden. Beim Versenden bekommt der Entwurf automatisch die nächste Angebotsnummer und das heutige Datum, die Gültigkeit (14/30/60 Tage) rechnet ab dann.

**Lead-Daten ändern:** In der Lead-Ansicht gibt es oben in der Karte „Daten“ den Knopf „Daten bearbeiten“ (Firma, Ansprechpartner, E-Mail, Telefon, Website, Branche, PLZ, Ort). Feld leeren = Angabe entfernen. Praktisch, wenn die E-Mail fehlt: eintragen, dann beim Angebot „Erneut per Mail senden“.

## Angebote: Nachfassen, Kopieren, Pflege und Auswertung (Oktober 2026)

- **Entwurf weiterbearbeiten:** „Bearbeiten und senden“ lädt jetzt den gespeicherten Entwurf (Positionen, Texte, „Das bekommt der Kunde“).
- **Angebot kopieren:** In der Angebotsliste des Leads und im Belege-Editor gibt es „Kopieren“ (neuer Entwurf mit denselben Positionen und Texten). Bei „+ Angebot an Neukunden“ kann man oben ein früheres Angebot als **Vorlage** wählen; der Firmenname im Text wird auf den neuen Empfänger umgestellt.
- **Erinnerung senden:** Bei einem verschickten Lead-Angebot gibt es „Erinnerung senden“ (kurze Nachfrage-Mail mit Angebot und neuem Link; der alte Link gilt dann nicht mehr). Erscheint auch im Verlauf des Leads.
- **Leistungstexte der Pakete pflegen:** Unter „Preise & Konditionen“ gibt es die Karte „Leistungstexte der Pakete“. Änderungen gelten für neue Angebote, versendete bleiben unverändert.
- **Belege-Editor:** Angebote an bestehende Kunden haben jetzt auch „Das bekommt der Kunde“ (mit Paket-Auswahl).
- **Bedingungen im Angebot:** Unter Einstellungen → Firmendaten gibt es „Bedingungen unter jedem Angebot“. Der Text erscheint im PDF und auf der Online-Seite. Bitte selbst festlegen und rechtlich prüfen lassen (AGB, Laufzeit, Kündigung, Zahlung).
- **Datenschutz:** Hast du eine eigene Datenschutzerklärung hinterlegt, erscheint unter Einstellungen → Rechtstexte ein Hinweis mit Knopf „Satz am Ende einfügen“, solange die Nutzungsstatistik dort nicht genannt wird.
- **Auswertung:** Auf „Angebote & Rechnungen“ steht oben die Karte „Angebote: Auswertung“ (verschickt, angesehen, angenommen, Quote, Zeit bis zur Annahme, Pakete).
- **Nutzung:** Unter Protokoll steht „Nie geöffnet“ und „Selten“ erst, wenn die Messung 14 Tage läuft (vorher wäre es Zufall).


## Zusagen aus dem AVV und wie das Portal sie umsetzt (Stand Oktober 2026)
- **Zwei-Faktor-Anmeldung für Admins ist Pflicht** (AVV Anlage 2). Ein Admin ohne 2FA kann sich anmelden, sieht aber nur die Einrichtungsseite, bis die Authenticator-App gekoppelt ist. Kunden- und Vertriebskonten: freiwillig. Notfall: `mkctl admin-reset <E-Mail>` setzt auch die 2FA zurück. Zum Abschalten der Pflicht (nicht empfohlen) `PORTAL_ADMIN_2FA=0` in der Umgebung des Portals setzen, dann steht aber der AVV-Text nicht mehr.
- **Aufbewahrung**: Chatverläufe 6 Monate (180 Tage), Audit-Log 12 Monate, Telefon-Zusammenfassungen 180 Tage, Sicherungen 30 Tage. Das läuft täglich automatisch und steht im Löschprotokoll. Das Audit-Log ist für die Anwendung unveränderlich; nur eine feste Datenbankfunktion löscht Einträge, die älter als 12 Monate sind.
- **Alte AVV (Version 1) ersetzen**: Beim Kunden erscheint ein Hinweis „Neue Fassung (Version 2) vorbereiten“, in der Übersicht „Heute“ steht „AVV: neue Fassung fehlt noch“. Der Dialog hat eine **Vorschau (PDF)**, ohne etwas zu speichern. Die alte Fassung bleibt als Nachweis liegen.
- **Änderung bei Unterauftragsverarbeitern ankündigen** (Einstellungen → „AVV: Änderung bei Unterauftragsverarbeitern ankündigen“): Anbieter, Leistung, Modul und Datum eintragen (mindestens vier Wochen Vorlauf, sonst lehnt das Portal ab). Betroffene Kunden bekommen eine Mail, im Kundenportal steht die Ankündigung unter „Datenschutz-Vertrag“ mit Knopf **Widerspruch einlegen** (bis zum Datum). Du bekommst bei Widerspruch eine Mail, in der Liste steht der Kunde mit Begründung. Die Anbieterliste änderst du erst zum angekündigten Datum, und nicht für Kunden, die widersprochen haben.
- **Überwachung und Wiederherstellungstest** liefen schon vorher: Prüfung alle 5 Minuten (Container, Portal von außen, Festplatte, Zertifikat, Sicherungsalter, Hintergrundjobs, Mailversand) mit Alarm per Mail und optional Telegram; wöchentlicher automatischer Wiederherstellungstest. Details und der Jahres-Probelauf: `docs/WIEDERHERSTELLUNG.md`.

## Domains, Freigaben mit Dateien und Versionen, Vertretung (Stand Oktober 2026)

**Domains pro Kunde.** Im Kundenblatt gibt es die Karte „Domains“: Domain, Registrar (Standard INWX), Inhaber (Kunde oder Markentrix) mit Name und Kontakt, Registrierung, Ablaufdatum, automatische Verlängerung, Jahrespreis, Status und Notiz. Auth-Codes werden bewusst nicht gespeichert. Wer in 60 Tagen abläuft, steht unter „Heute“ (als Aufgabe, ohne Doppelungen). Die Domains landen im Datenexport beim Offboarding, die Jahrespreise in der Kostenübersicht. Beim AVV schlägt das Portal Domains vor, die Markentrix bei INWX für den Kunden hält. Im Onboarding gilt der Schritt „Domain erfasst“ automatisch als erledigt, sobald Inhaber und Ablaufdatum eingetragen sind.

**Freigaben mit mehreren Dateien.** Im Kundenblatt unter „Freigaben“ → „Neue Freigabe-Bitte“: Titel, Art, Text, beliebig viele Bilder oder PDFs anhängen, optional geplante Veröffentlichung. Der Kunde bekommt eine Mail mit Link; im Portal sieht er dasselbe.

**Vorlagen.** Über das Auswahlfeld „Vorlage wählen“ füllst du Titel und Text vor (fünf Standardvorlagen sind angelegt, zum Beispiel Social-Post Wochenangebot). „Als Vorlage speichern“ legt eigene an, „Vorlage löschen“ entfernt sie.

**Freigabe per Mail-Link ohne Anmeldung.** Der Link ist 14 Tage gültig und führt auf eine Seite mit Text, Bildern und zwei Knöpfen („Freigeben“ / „Änderung wünschen“). Pflicht ist der volle Name; bei einer Änderung zusätzlich eine Begründung. Gespeichert werden Datum, Uhrzeit, Name, IP-Adresse und der Vermerk „per Link“. Im Link steht nur ein Zufallswert, in der Datenbank liegt nur dessen Prüfsumme. Ist der Link abgelaufen, kann der Kunde sich im Portal anmelden oder ihr schickt eine neue Bitte.

**Versionen.** Wünscht der Kunde Änderungen, steht in der Liste „Neue Version senden“. Die Überarbeitung geht als Version 2, 3 … an den Kunden, der frühere Kommentar steht dabei. Pro Ablehnung gibt es genau eine neue Version; der geplante Termin wird übernommen.

**Freigabe-Kalender.** Unter „Freigaben“ oben: die nächsten 14 Tage mit allen geplanten Veröffentlichungen, gelb = wartet, grün = freigegeben, rot = Änderung gewünscht, darunter wartende Freigaben ohne Termin. Fehlt eine Freigabe zwei Tage vor dem Termin, erscheint unter „Heute“ eine Aufgabe „jetzt anrufen“.

**Telefonat nach 5 Tagen.** Reagiert ein Kunde fünf Tage nicht auf eine Freigabe, schlägt „Heute“ einen Anruf vor (mit Telefonnummer als Direktlink).

**Vertretung.** Der Inhaber trägt unter Konto → Vertretung eine zweite Person mit Zeitraum ein (zum Beispiel Urlaub). Nur in diesem Zeitraum bekommt sie die Freigabe-Mails zusätzlich. Eine Entscheidung per Link zählt wie jede andere und wird mit dem Namen festgehalten.

**Vertragsstand.** Unter Verwaltung zeigt „Vertragsstand“ auf einen Blick, ob die Zusagen aus dem AVV eingehalten werden: 2FA, Audit-/Chat-Aufbewahrung, Sicherung, Restore-Test, AVV-Fassung, Widersprüche, ablaufende Domains.

**Bewertungsanfrage und Monatsbericht** gab es schon: Der Monatsbericht geht automatisch per Mail raus, die Bewertungsanfrage nach einem erledigten Termin verschickst du bewusst selbst über deinen eigenen Kanal.

## App auf dem Handy installieren (Android und iPhone)

Das Portal ist eine installierbare Web-App. Es gibt keine eigene APK-Datei und keinen App-Store-Eintrag. Deshalb ist sie immer sofort auf dem neuesten Stand, Updates muss niemand einspielen.

- **Android:** In **Google Chrome** das Menü ⋮ öffnen und „App installieren“ wählen. Nicht über andere Browser (Samsung Internet, Opera, Vivaldi …) und nicht über eine heruntergeladene Datei installieren: Das erzeugt teils eine App, die Google Play Protect als „unsichere App blockiert“ meldet. Eine schon so angelegte App einfach löschen und über Chrome neu installieren.
- **iPhone:** In **Safari** auf das Teilen-Symbol tippen, „Zum Home-Bildschirm“, „Hinzufügen“. Erst dann sind auch Benachrichtigungen möglich.
- Im Portal steht dieselbe Anleitung unter Konto bzw. Einstellungen in der Karte „App & Benachrichtigungen“, passend zum Gerät. Öffnet jemand das Portal in einem anderen Android-Browser, weist die Karte auf Chrome hin.
- Echte Store-Apps (Google Play, Apple App Store) wären nur mit Entwicklerkonten möglich (Google einmalig ca. 25 US-Dollar, Apple ca. 99 US-Dollar pro Jahr) und einem eigenen Paket pro Store. Das Portal bräuchte dafür keine Änderung, nur einen Einpack-Schritt.

### So führst du Kunden und Vertriebler durch die Installation

1. **Einladung:** Die Einladungs-Mail nennt schon den richtigen Browser (Android: Chrome, iPhone: Safari) und die beiden Installationsschritte.
2. **Erster Login:** Beim allerersten Anmelden öffnet sich automatisch die Seite „So geht’s“, mit Bildern in Schritten: Teil 1 die App aufs Handy legen (Reiter Android/iPhone, vorgewählt nach Gerät), Teil 2 so arbeitest du im Portal. Kunden und Vertriebler bekommen **unterschiedliche** Anleitungen: Der Kunde sieht Heute, Freigaben, Anfragen, Nachrichten und Menü; der Vertriebler zusätzlich Anrufliste, Ergebnis festhalten, Leads, Pipeline, Angebotsanfragen, Zahlen, Provisionen und Leitfaden. Mit „Los geht’s“ ist sie erledigt und kommt nicht von allein wieder. Wiederfinden: Menü → „So geht’s“.
3. **Banner:** Solange die App am Handy noch nicht installiert ist, steht oben ein kleines Banner „Markentrix als App aufs Handy legen“ mit Link zur Anleitung. Es lässt sich wegklicken, am Rechner erscheint es nie.
4. **QR-Code:** Im Kundenblatt und beim Vertriebler gibt es die Karte „Portal aufs Handy“: QR-Code zum Scannen mit der Handy-Kamera, dazu „Text mit Link kopieren“ und „Per WhatsApp senden“.
5. **Falscher Browser:** Öffnet jemand das Portal auf Android in Samsung Internet, Opera oder Vivaldi, weist die Karte „App & Benachrichtigungen“ auf Chrome hin.

## Website-Dienste: Formular, Termine, PayPal, Bewertungen (Stand Oktober 2026)
Unsere Kunden-Websites (von uns gebaut, auf unserem Server, Domains bei INWX) nutzen vier Dienste. Der Kunde (Inhaber) trägt seine Daten unter **Website-Dienste** im Kundenportal ein, wir bauen die Bausteine ein.

**Leistungen, Anzahlung, Zahlungsstand, Excel (Kundenportal → Website-Dienste):**
- Je Leistung: Dauer (Pflicht), Pause, Preis, Anzahlung (fester Betrag oder Prozent vom Preis) und das Häkchen „bestätige ich selbst“. Hat die Leistung eine Anzahlung, bekommt der Besucher den PayPal-Link sofort in der Mail, auch bei Sofortbuchung. Bei „bestätige ich selbst“ ist die Zeit nur vorgemerkt, bis der Inhaber bestätigt.
- „Anzahlung und Absage“: Kostenlos absagen bis X Stunden vorher (Standard 24), danach ist der volle Betrag zu zahlen. Optional eine Frist für die Anzahlung: Ist bis dahin nichts als erhalten markiert, gibt das Portal den Termin frei und informiert Besucher und Betrieb.
- Beim Termin klickt der Inhaber **„Anzahlung erhalten“** und später **„Alles bezahlt“**. Das Portal sieht PayPal nicht, die Markierung stammt vom Inhaber.
- **Absage und Umbuchen durch den Besucher:** Der Link in der Mail zeigt erst die Regel und sagt erst nach einem Klick ab. Bis zur Frist (Standard 24 Std.) ist es kostenlos und der Besucher kann stattdessen einen neuen Termin wählen. Danach ist der volle Betrag fällig, die Anzahlung bleibt beim Betrieb.
- **Erstattung:** Bei rechtzeitiger Absage oder wenn der Betrieb absagt, erscheint „Anzahlung zurückzahlen“. Nach der Rückzahlung per PayPal klickt der Inhaber **„Erstattet“**.
- **Quittung:** Beim Termin mit erhaltener Anzahlung: **„Quittung (PDF)“** oder **„Quittung per Mail“**. Es ist eine Zahlungsbestätigung, keine Rechnung mit Umsatzsteuer; die steuerliche Behandlung klärt die Steuerberatung.
- **Zusatzfragen je Leistung:** Feld „Zusatzfragen“, z. B. `Haarlänge*, Haarzustand` (Stern = Pflicht). Die Website zeigt sie im Formular.
- **Mehrere Leistungen in einem Termin:** Dauer, Preis und Anzahlung werden addiert; die Person muss alle Leistungen anbieten.
- Datenschutz-Texte für Zahlung/Anzahlung/Gutschein: `docs/DATENSCHUTZ-BAUSTEIN-ZAHLUNG.md` (vom Anwalt prüfen lassen).
- **Übersicht als Excel:** Woche, Monat oder eigener Zeitraum. Blätter: Termine (mit Preis, Anzahlung, Zahlungsstand, Rest), Zusammenfassung, Gutscheine.
- Leistungen, Preise und Dauer stehen automatisch in der Wissensdatenbank (Eintrag „Leistungen und Preise (automatisch)“) und im Baustein `data-mk="preise"` der Website. Im Kundenblatt (Admin) stellst du je Kunde ein, ob seine Änderungen **sofort live** gehen (Standard) oder **deine Freigabe** brauchen (Karte „Leistungen und Preise: Freigabe“).

**Gutscheine (Kunden-Websites):** Fragt ein Besucher über das Formular einen Gutschein an (`typ=gutschein`), erscheint er im Kundenportal unter Website-Dienste → **Gutschein-Anfragen**. Der Inhaber klickt **„Zahlungslink senden“** (braucht den PayPal.Me-Link bei PayPal; Betrag aus der Anfrage oder von Hand) und, sobald das Geld da ist, trägt er einen Code ein und klickt **„Gutschein senden“**. Beide Mails gehen im Namen des Betriebs raus. Das Portal sieht PayPal-Zahlungen nicht, deshalb prüft der Inhaber den Zahlungseingang selbst. Gilt für jede Kunden-Website ohne Änderung an der Seite.

**Einbau in die Website** (Admin → Kunde → Karte „Website-Dienste“ zeigt den fertigen Code zum Kopieren):
`<script src="https://portal.markentrix.de/static/js/site.js" data-site="mk_…" defer></script>` einmal vor `</body>`, dann je Dienst `<div data-mk="kontakt|termin|bewertungen"></div>` und `<div data-mk="paypal" data-betrag="49,90" data-titel="Gutschein"></div>`. Die Seite enthält nie ein Passwort.

- **Kontaktformular:** Anfragen landen im Kundenportal unter „Anfragen“ und per E-Mail beim Kunden (Antwort-an = Besucher). Standard: Versand über unseren Mailserver mit dem Firmennamen als Absendername. Optional eigenes Postfach des Kunden (Gmail, GMX, Telekom, IONOS …): Server und Port werden aus der Adresse vorbelegt, die Verbindung wird vor dem Speichern geprüft, bei späteren Fehlern springen wir automatisch auf unseren Versand zurück (im Status sichtbar).
- **Terminbuchung:** Der Kunde fügt die geheime iCal-Adresse seines Kalenders ein (Google, Outlook, iCloud, IONOS …). Belegte Zeiten (auch wiederkehrende, ganztägige, andere Zeitzonen) werden nicht angeboten. Buchungen erscheinen in „Heute“/„Termine“ des Kunden, beide Seiten bekommen eine E-Mail mit Kalender-Einladung, Besucher können per Link absagen.
- **PayPal:** Nur die öffentliche Client-ID (oder ein PayPal.Me-Link). Das Geld geht direkt an den Kunden, wir verarbeiten keine Zahlungen.
- **Google-Bewertungen:** Place-ID des Kunden; wir holen mit **einem** Places-API-Schlüssel von uns (Admin → Einstellungen → „Google-Bewertungen“) alle 12 Stunden Sterne und die neuesten Bewertungen. Ohne Schlüssel tragen Kunden Sterne und Anzahl von Hand ein.

- **Google Analytics:** Der Kunde trägt die Mess-ID (G-…) ein. Das Skript zeigt automatisch eine Abfrage „Statistik erlauben?“ und lädt Google erst nach Zustimmung (Wahl wird im Browser gemerkt, Widerruf über `<span data-mk="cookies"></span>`, z. B. im Footer). Hat die Website schon ein eigenes Cookie-Banner, die Mess-ID dort statt hier einbinden und den Dienst ausgeschaltet lassen.

**Sicherheit:** Zugangsdaten (SMTP-Passwort, Kalender-Adresse) werden mit dem Server-Schlüssel (`PORTAL_SECRET`) verschlüsselt, sind nie wieder lesbar (auch nicht für Admins) und nur vom Inhaber ersetzbar. Die öffentlichen Aufrufe (`/site/<ID>/…`) funktionieren nur von den Domains des Kunden (Domainverwaltung bzw. Websites), sind je IP und je Website begrenzt und haben ein Lockfeld gegen Bots. SMTP-Server und Kalender-Adressen werden nur geholt, wenn sie ins öffentliche Internet zeigen (kein Zugriff auf interne Dienste), Kalender nur über https. Gebuchte Termine werden 180 Tage nach dem Termin gelöscht, das Ereignisprotokoll nach 90 Tagen.

**Vor dem ersten Kunden:** Domain des Kunden in der Domainverwaltung eintragen (sonst lehnt der Server die Website ab); Datenschutzerklärung der Website um Kontaktformular, Terminbuchung und ggf. Google-Bewertungen/PayPal ergänzen; AVV-Beschreibung der Leistungen und Anlage 3 (Unterauftragsverarbeiter: Google Places) vom Anwalt prüfen lassen (docs/ANWALT-CHECKLISTE.md).

**Papierkorb:** Gelöschte Seiten liegen 14 Tage im Papierkorb (Websites & Demos, ganz unten). Dort gibt es „Wiederherstellen“, „Endgültig löschen“ (je Eintrag, mit Rückfrage) und „Papierkorb leeren“. Endgültig gelöscht ist nicht rückholbar, nur noch aus einer Sicherung.

**Demo-Adresse bei bestehendem Caddy:** `install.sh` legt `demo.<domain>` im vorhandenen Caddy selbst an (Datei im Caddy-Ordner), sofern dort noch kein Block dafür steht. Ohne diesen Eintrag zeigt der Browser bei Demos „ERR_SSL_PROTOCOL_ERROR“. Nachträglich: `mkctl caddy-neu`.

**Agentur-Standard (Fristen, Bericht, Startpaket):**
- **Änderungswünsche haben eine Frist:** „Änderung“ 3 Werktage, „Problem“ 2 Werktage ab Eingang. Der Kunde sieht unter Nachrichten „bis <Datum>“ und nach Erledigung „erledigt am <Datum>“. Ist die Frist überschritten, erscheint es in der Frühwarnung des Kunden (Admin → Start).
- **Monatsbericht** enthält jetzt „Was wir für Sie erledigt haben“ (erledigte Änderungen, Aufträge, Probleme und Website-Updates des Monats).
- **Livecheck** prüft zusätzlich Bild-Beschreibungen, Hauptüberschrift, Favicon und einen Telefon-/Mail-Link (nur Hinweise, die Ampel bleibt dadurch grün).
- **Vertrag:** Der Onboarding-Punkt „Angebot/Vertrag unterschrieben“ hakt sich selbst ab, sobald ein Angebot als angenommen markiert ist. Hat der Kunde einen im Portal bereitgestellten AVV nach 3 Tagen nicht bestätigt, bekommt er eine höfliche Erinnerung (höchstens zwei, alle 3 Tage).
- **Startpaket (Kunde öffnen → Onboarding-Checkliste → „Startpaket auslösen“):** legt Checkliste und die ersten Team-Aufgaben mit Fristen an (AVV, Material, Briefing, Domain falls Website-Modul, Abnahme-Termin) und schickt einmalig die Willkommensmail mit den Wünschen an den Kunden. Mehrfach klickbar, nichts wird doppelt angelegt.

**Statusseite der Plattform (nur für Angemeldete):** `https://portal.<domain>/status` ist nur sichtbar, wer im Portal angemeldet ist (Kunden, Vertriebler, Team); wer nicht angemeldet ist, landet bei der Anmeldung. In der Fußzeile jedes Portals steht der Link „Systemstatus“. Die Seite zeigt automatisch Portal, Datenbank, Kunden-Websites (nur „x von y erreichbar“, keine Namen), E-Mail-Versand, Datensicherung (gelb, wenn älter als 2 Tage) und die Erreichbarkeit der letzten 30 Tage. Störungen und Wartungen trägst du im Admin unter **Websites & Demos → Statusseite** ein und beendest sie dort wieder; sie erscheinen oben und danach 30 Tage im Verlauf. Eine geplante Wartung bleibt grün, bis sie beginnt. Die Seite lädt alle 2 Minuten neu. Die Statusseite je Kunde (geheimer Link) bleibt davon unberührt.

**Kunde informieren, wenn die Website online ist:** Beim Hochladen einer Live-Website (und bei „Live schalten“ einer Demo) ist der Haken „Kunden per Mail und Glocke informieren“ standardmäßig an. Optional trägst du ein, was geändert wurde; das steht dann in der Mail. Der Kunde bekommt die Nachricht erst, wenn die Seite wirklich erreichbar ist (der Server-Dienst hat veröffentlicht und die Prüfung meldet „erreichbar“): bei einer neuen Website also erst nach der DNS-Umstellung („Ihre neue Website ist online“), bei einem Update meist innerhalb von 1–2 Minuten („Ihre Website ist aktualisiert“). Dazu kommt eine Meldung in der Glocke und per Push im Kundenportal. Nichts wird doppelt gesendet; schlägt das Veröffentlichen fehl, geht keine Mail raus. Demos lösen nie eine Mail aus. Hat der Kunde Benachrichtigungen abgeschaltet, bleibt es still.

## Website als ZIP hochladen (Admin → Websites & Demos → „Website hochladen“)
So veröffentlichst du eine fertige Kunden-Website, ohne SSH oder WinSCP:
1. Website als ZIP packen. Entweder die fertige Website (`index.html` oben) oder ein ganzes Projekt: Das Portal findet den Website-Ordner selbst (bevorzugt `website-fertig`, `dist`, `public`, sonst den höchsten Ordner mit `index.html`) und übernimmt nur diesen. Server-Code, Build-Skripte, Docker-Dateien und Doku bleiben draußen. Nach dem Hochladen steht, aus welchem Ordner die Dateien kamen.
2. Im Admin **Websites & Demos** → **Website hochladen**: Art (Live oder Demo), Domain ohne www (z. B. `elbdetail.de`), **Kunde mit Kundennummer** (MK-1001 · Firma; die Domain des Kunden wird vorgeschlagen), ZIP wählen, **Hochladen und veröffentlichen**.
   **Mehrere ZIPs (Zip 1 + Zip 2):** Beim Auswählen mehrere ZIP-Dateien gleichzeitig markieren (bis 10). Sie werden in der gewählten Reihenfolge zu einer Website zusammengeführt, gleichnamige Dateien aus einer späteren ZIP ersetzen frühere; mindestens eine ZIP braucht die `index.html`. Bei einem Fehler nennt die Meldung die betroffene ZIP, dann wird nichts veröffentlicht.

3. Das Portal prüft die ZIP (keine Skripte wie .php/.exe, keine Symlinks, keine unsicheren Pfade, keine versteckten Dateien, Größenlimits: 120 MB ZIP, 400 MB entpackt) und legt einen Auftrag ab. Der Server-Dienst (läuft jede Minute) richtet bei einer neuen Domain den Webserver-Eintrag für `domain` und `www.domain` ein (HTTPS-Zertifikat automatisch, sobald die Domain per A-Eintrag auf den Server zeigt) und schaltet die Seite live. Das Ergebnis erscheint unter dem Formular, mit Link zur Seite.
4. Haken „Website-Dienste automatisch einbauen“: fügt das Skript für Formular, Termine, Bewertungen und Statistik (Cookie-Abfrage) vor `</body>` jeder HTML-Seite ein, mit der Kennung dieses Kunden. Die Bausteine selbst (`data-mk=…`) setzt du dort, wo sie erscheinen sollen (Code im Kundenblatt → Website-Dienste).

**Aktualisieren:** Dieselbe Domain nochmal hochladen. Die vorige Version wird gesichert (die letzten 3, höchstens 30 Tage), die Wochenangebote des Kunden (`angebote/`) und die Kennung bleiben erhalten. **Vorige Version zurückholen** (Name oben eintragen) stellt sie in einer Minute wieder her, ein weiterer Klick wechselt zurück.

**Zuordnung:** Die Website wird dem Kunden zugeordnet (Kundenblatt → Websites, Domain beim Kunden vermerkt, Website-Dienste erlauben genau diese Domain) und trägt Kundennummer und Firma in ihrer Kennung (`site.json`). Domain bei IONOS/INWX: nur der A-Eintrag (und www) muss auf den Server zeigen, siehe oben.

Der alte Weg `mkctl site-add … --from Ordner` funktioniert weiter. Eine Windows-.bat mit SSH ist nicht mehr nötig.


## Website-API: Termine, Anfragen und Statistik für jede Kunden-Website (Friseur, Werkstatt, Praxis …)

Jede fertige Website ruft unter ihrer eigenen Domain `/api/anfrage`, `/api/slots`, `/api/verfuegbarkeit` und `/api/e` auf. Die Domain wird beim Hochladen eingerichtet, Caddy leitet genau diese Pfade ans Portal, das Portal erkennt den Kunden an der Domain. Es gibt pro Kunde kein eigenes Backend und keinen eigenen Admin: Alles pflegt der Inhaber im Kundenportal unter **Website-Dienste**. Vertrag und Grenzen: `docs/WEBSITE-API.md`. Prompt für Claude Code, damit jede neue Seite passt: `docs/WEBSITE-PROMPT.md`.

**Einrichtung für einen Kunden mit Terminbuchung (z. B. Friseursalon):**
1. Website nach dem Prompt bauen lassen, ZIP im Admin hochladen (Websites & Demos → Website hochladen, Kunde und Domain wählen). Ganze Projektordner sind ok, der Ordner `website-fertig` wird automatisch gefunden.
2. Im Kundenportal (oder für den Kunden) **Website-Dienste**: Kontaktformular einschalten (Empfänger), Terminbuchung einschalten. Dort einstellen: Öffnungstage, Beginn/Ende und Dauer **oder** feste Uhrzeiten, Höchstzahl pro Tag, Vorlauf, Ort, optional den iCal-Kalender.
3. „Ich bestätige jede Buchung selbst“ ein: Neue Wünsche sind vorgemerkt und warten unter „Buchungen über die Website“ auf **Bestätigen** (mit optionaler Anzahlung und PayPal.Me-Link) oder **Ablehnen**. Aus: Buchungen gelten sofort, der Kunde bekommt die Einladung automatisch.
4. Urlaub und Feiertage unter **Urlaub und Sperrtage** eintragen. Unbestätigte Reservierungen geben die Zeit nach der Haltefrist (Standard 72 Stunden) wieder frei.
5. **Leistungen und Mitarbeiter** (Friseur, Kosmetik, Praxis): Unter „Leistungen und Mitarbeiter“ jede Leistung mit Dauer und Pause eintragen (Herrenschnitt 30 Min., Färben 120 Min. + 15 Min. Pause) und jede Person mit Arbeitstagen, Zeiten, eigenem Kalender und den Leistungen, die sie anbietet. Die Website fragt die Listen unter `/api/leistungen` und `/api/mitarbeiter` ab und bietet nur Zeiten an, in denen die gewünschte Person (oder irgendjemand bei „egal“) die ganze Dauer Zeit hat. Urlaub einer einzelnen Person unter „Urlaub und Sperrtage“ mit „Gilt für“.
6. Besucherzahlen (ohne Cookies) stehen unter „Besucher der letzten 30 Tage“.

**Wichtig:** Die Uhrzeiten, die die Website anbietet, müssen zu den „Festen Uhrzeiten“ im Portal passen. Bestehende Websites bekommen die Weiterleitung automatisch (der Server-Dienst ergänzt unveränderte Standard-Einträge innerhalb einer Minute).

## Betrieb der Kunden-Websites: Erinnerungen, Wachdienst, Vorschau-Freigabe, Sicherung (Stand Oktober 2026)
**Terminerinnerungen an die Besucher.** Das Portal schickt jedem Besucher mit gültiger Buchung eine E-Mail 24 und 2 Stunden vorher (mit Ort, Leistung, Mitarbeiter und Absage-Link). Der Kunde ändert die Zeiten oder schaltet sie ab unter Website-Dienste → Terminbuchung (0 = aus). Wer erst kurz vor dem Erinnerungszeitpunkt gebucht hat, bekommt keine zweite Mail direkt nach der Bestätigung.

**Nichterschienen-Zähler.** Unter Buchungen steht „Vergangene Termine – hat es geklappt?“ mit zwei Knöpfen. Das Ergebnis erscheint in der Statistik und im Monatsbericht; bei Besuchern, die schon einmal nicht kamen, steht „1× nicht erschienen“. Der Termin im Portal bekommt den Status „erledigt“ bzw. „nicht erschienen“.

**Wachdienst.** Alle fünf Minuten prüft der Server jede Live-Website: Startseite, Website-API (`/api/health`, beweist die Weiterleitung von Caddy zum Portal) und Zertifikat. Nach zwei Fehlschlägen in Folge kommt eine Mail (und Push) an die Alarm-Adresse unter Einstellungen → Benachrichtigungen; bei Erholung eine Entwarnung. Zertifikate mit weniger als 14 Tagen Rest werden alle 3 Tage gemeldet. Eine frisch veröffentlichte Seite, deren Domain noch nicht auf den Server zeigt, löst keinen Alarm aus. Den Stand sieht man in Admin → Websites & Demos (Spalte Status) und der Kunde in den Website-Diensten; die Erreichbarkeit der letzten 30 Tage steht außerdem im Monatsbericht.

**Vorschau vom Kunden freigeben lassen.** Admin → Websites & Demos → „Vorschau vom Kunden freigeben lassen“: Demo und Kunde wählen. Der Kunde bekommt eine Mail mit Link (ohne Anmeldung, 14 Tage gültig), sieht die Demo-Adresse und klickt auf „Freigeben“ oder „Änderung wünschen“. Name, Zeit und IP werden festgehalten; der Stand steht in der Websites-Liste und unter Freigaben.

**Website aus der Tagessicherung zurückholen.** Admin → Websites & Demos → „Aus Tagessicherung wiederherstellen“: Seite und Datum wählen. Der Server holt nur diese Seite aus der Nachtsicherung (`sites.tar.gz`), die jetzige Version bleibt als Vorversion erhalten (wieder holbar über „Vorige Version zurückholen“), die aktuellen Wochenangebote bleiben. Termine, Anfragen und Einstellungen in der Datenbank werden nicht verändert; dafür gilt weiterhin die Datenbanksicherung (Anleitung im Abschnitt Sicherung; prüfbar mit `mkctl restore-test`).


## Mail-Zustellbarkeit, Kunden-Frühwarnung, Datenexport, Kündigung, Daten aus der Sicherung (Stand Oktober 2026)
**Mail-Zustellbarkeit (Admin → Einstellungen → „Mail-Zustellbarkeit“).** Jeder Versand wird mit Ergebnis protokolliert (nur die Empfänger-Domain, nie die Adresse; 90 Tage). Täglich gegen 5 Uhr prüft der Server SPF, DKIM und DMARC der Absender-Domain und der eigenen Kunden-Postfächer; bei Problemen mit deiner Absender-Domain kommt eine Push-Nachricht. DKIM wird über die üblichen Selektoren gesucht; hat dein Anbieter einen eigenen, kann „fehlt“ ein Fehlalarm sein. Rückläufer, die der Zielserver erst später meldet, sieht das Portal nicht. Der Kunde sieht dasselbe für sein eigenes Postfach unter Website-Dienste („Kommen die Mails an?“).

**Kunden-Frühwarnung** (Übersicht) kennt jetzt zusätzlich: Website seit über einer Stunde nicht erreichbar, drei oder mehr nicht zugestellte Mails pro Woche, Freigabe wartet seit über 7 Tagen, Kündigungswunsch eingegangen (sofort Stufe „hoch“).

**Meine Daten und Kündigung (Kundenportal → Einstellungen, nur Inhaber).** „Meine Daten herunterladen“ liefert eine ZIP mit Anfragen, Terminen, Rechnungen und Berichten als PDF, Dokumenten und den Dateien der Website (ohne interne Team-Notizen; höchstens dreimal pro Stunde). Die Kündigung im Portal ist verbindlich (Textform): Das Vertragsende wird aus der Kündigungsfrist (Admin → Einstellungen → „Kündigung durch Kunden“, Standard 30 Tage) und der Mindestlaufzeit der Buchungen berechnet, jeweils zum Monatsende; ein späterer Wunschtermin gilt. Der Kunde sieht das Ende schon vor dem Absenden und bekommt sofort eine Bestätigung per Mail, du eine Mitteilung. Versehentliche Kündigungen kann er 24 Stunden lang zurücknehmen. Zum Vertragsende setzt der Server den Kunden automatisch auf „gekündigt“ und beendet die Buchungen; danach übergibst du Domains und löschst wie gewohnt (Kunde → Vertragsende). Offene Kündigungen erscheinen in der Frühwarnung.

**Daten eines einzelnen Kunden aus der Datenbanksicherung zurückholen (Admin → Kunde → „Daten aus der Sicherung zurückholen“).** Sicherung wählen, „Sicherung prüfen“: der Server lädt die Sicherung in eine Wegwerf-Datenbank und liest nur die Zeilen dieses Kunden aus (Minuten). Du siehst je Bereich, wie viele Zeilen damals da waren und heute fehlen, und holst gezielt zurück. Es werden nur fehlende Zeilen eingefügt, nichts überschrieben oder gelöscht; Zugangsdaten, Protokolle und Dateien/Dokumente (bytea) sind ausgenommen. Der Auszug enthält personenbezogene Daten und wird nach dem Zurückspielen oder spätestens nach einem Tag gelöscht.


## Livegang-Hilfen, Bewertungsanfragen, Wartungsverträge, Ladezeit-Prüfung (Stand Oktober 2026)
**DNS-Assistent (Admin → Websites & Demos → Spalte „DNS“ → „DNS prüfen“).** Zeigt, wohin die Domain (und www) heute zeigt, erkennt typische Anbieter (Squarespace, Wix, Shopify, IONOS, …), meldet fremde IPv6-Einträge (AAAA), die Besucher und Zertifikat ins Leere führen, und liefert eine fertige Mail für den Kunden zum Kopieren. Die Server-Adresse ermittelt der Server stündlich selbst; mit eigener Adresse (z. B. hinter einem Load-Balancer) in der `.env` `SERVER_IPV4=…` setzen. Alle 10 Minuten werden Live-Domains, die noch nicht stimmen, neu geprüft; sobald eine Domain auf den Server zeigt, bekommst du einmal eine Push-Nachricht „Domain ist live“.

**Neue Seite wartet auf DNS.** Eine frisch veröffentlichte Seite, deren Domain noch nicht auf den Server zeigt, steht als „wartet auf DNS“ (gelb) und löst keinen Ausfall-Alarm aus. „Jetzt prüfen“ in der Zeile testet sofort DNS, Startseite, Website-API und Zertifikat. Sobald die Seite erreichbar ist, kommt eine Push-Meldung „Website ist live“.

**DNS-Anleitung an den Kunden mailen.** Im DNS-Fenster schickt „An Kunden mailen“ die fertige Anleitung an den Kunden. Stimmt die Domain nach 3 Tagen noch nicht, erinnert der Server automatisch (höchstens zweimal, nur an Werktagen).

**Sicherheit (Einstellungen).** Übersicht, welche Admin- und Vertriebs-Zugänge die Zwei-Faktor-Anmeldung haben. Für Vertriebs-Zugänge lässt sie sich zur Pflicht machen (dann sehen sie bis zur Einrichtung nur die Einrichtungsseite); bei Admins ist sie immer Pflicht.

**Onboarding-Checkliste.** Neu: Schritte „DNS zeigt auf den Server“ und „Google-Unternehmensprofil geprüft“; „DNS“ und „Erste Rechnung gestellt“ werden automatisch erkannt. Auf dem Start-Bildschirm zeigt die Liste je Kunde den nächsten Schritt und markiert Kunden, bei denen seit 7 Tagen nichts abgehakt wurde, als „hängt“.

**Vorhandener Caddy (z. B. Container „server-caddy-1“).** `install.sh` erkennt den Container und den Ordner, aus dem er Domain-Dateien liest (`/etc/caddy/sites`, auf dem Server z. B. `/srv/caddy-sites`), und merkt sich beides. Neue Kunden-Websites schreibt der Server-Dienst dann dorthin und lädt den Caddy neu. Sobald die DNS einer Domain stimmt, wird der Caddy noch einmal neu geladen, damit er das Zertifikat sofort holt. Klappt der Reload nicht, steht das in der Upload-Meldung; Abhilfe auf dem Server: `mkctl caddy-neu`. Der Selbsttest (`mkctl selbsttest`, läuft auch am Ende jedes Updates) prüft, ob die Webserver-Konfiguration gültig ist und ob jede Kunden-Domain lokal mit Zertifikat ausgeliefert wird. Zeigt eine Domain noch nicht auf den Server, ist das nur eine Warnung; zeigt sie auf den Server und es klappt trotzdem nicht, ist es ein Fehler mit Alarm-Mail.

**Livegang-Check.** Beim Hochladen einer Seite und per Knopf „Check“ in der Liste: Impressum und Datenschutz verlinkt, Titel, Beschreibung, Viewport, tote Verweise und Bilder, Bilder über 1,5 MB, http-Verweise, localhost, Platzhaltertext, Formular ohne Ziel, Google Fonts/Analytics/Facebook/Maps/YouTube (Hinweis für die Datenschutzerklärung). Ampel grün/gelb/rot; der Upload wird nie blockiert, du siehst nur die Liste.

**Bewertungsanfrage nach dem Termin (Kunde → Website-Dienste → Google-Bewertungen).** Opt-in je Kunde. Markiert der Kunde einen Termin als „erschienen“, bekommt der Besucher nach der gewählten Zeit (1 bis 72 Stunden) eine Mail mit dem Bewertungs-Link und einem Abmeldelink. Abgemeldete Adressen erhalten für diesen Kunden nie wieder eine Anfrage. Voraussetzung: Place-ID oder Link „Rezension schreiben“ hinterlegt.

**Wartungsverträge (Admin → Kunde → „Wartungsvertrag & wiederkehrende Rechnungen“).** Plan mit Turnus (monatlich, vierteljährlich, halbjährlich, jährlich), Positionen aus den aktiven Buchungen (Monatspreis mal Turnus, abzüglich Rabatt) oder fest, Startdatum und optionalem Ende. Der Server erzeugt gegen 6 Uhr am Stichtag die Rechnung für den folgenden Zeitraum, stellt sie aus (Rechnungsnummer, Fälligkeit nach deinem Zahlungsziel) und sendet sie auf Wunsch automatisch an den Kunden; sonst bekommst du eine Push-Nachricht und versendest unter Belege. Pro Zeitraum entsteht nur eine Rechnung. Referenzkunden, nicht aktive Kunden und Kunden nach Vertragsende werden nicht abgerechnet; Voraussetzung sind vollständige Firmendaten inkl. Steuernummer oder USt-IdNr. Ein Rückstand wird mit bis zu drei Rechnungen pro Lauf nachgeholt. „Jetzt erzeugen“ löst die nächste Rechnung sofort aus.

**Ladezeit und tote Links.** Täglich ruft der Wachdienst die Startseite und bis zu 25 interne Seiten jeder Live-Website ab. Ergebnis (typische Ladezeit, tote Verweise, langsame Seiten über 3 Sekunden) steht in der Websites-Liste, in der Kunden-Statistik und im Monatsbericht. Neue tote Verweise melden dir Mail und Push.


## Statusseite, Zahlungsverzug, Preiserhöhung, Empfang-Zugang, Selbsttest (Stand Oktober 2026)
**Selbsttest (`mkctl selbsttest`).** Läuft automatisch am Ende von `install.sh` und kann jederzeit von Hand gestartet werden. Er prüft: Container, Portal und Anmeldung, Datenbank, Anmeldung am Mail-Server (es wird keine Mail gesendet), Website-API, Hintergrundaufgaben, den Server-Dienst für Aufträge (Cron), Alter der Sicherung, Erreichbarkeit von außen und Speicherplatz. Bei Fehlern geht eine Alarm-Mail an dich; der Exitcode ist dann 1.

**Statusseite (Kunde → Einstellungen → „Statusseite für deine Website“).** Der Inhaber schaltet sie ein und bekommt einen geheimen Link (`/status/…`). Die Seite zeigt je Domain: erreichbar oder gestört, Erreichbarkeit der letzten 30 Tage, Zertifikat, typische Ladezeit, defekte Verweise, letzte Veröffentlichung, außerdem die letzte tägliche Sicherung und die letzten Änderungen. Keine Rechnungen, keine Anfragen, keine Namen. Ein neuer Link macht den alten ungültig; bei gekündigten Kunden ist die Seite aus.

**Zahlungsverzug (Admin → Einstellungen → Zahlung & Mahnwesen → „Bei langem Zahlungsverzug“).** Du legst fest, nach wie vielen Tagen nach der 2. Mahnung der Wartungsplan des Kunden pausiert wird (0 = nie). Optional pausiert das Portal zusätzlich Formular und Terminbuchung der Kunden-Website; die Seite selbst bleibt online, Besucher sehen dort eine höfliche Fehlermeldung. Sobald nichts Überfälliges mehr offen ist, wird automatisch alles wieder freigegeben. Von Hand pausierte Pläne bleiben pausiert. Du bekommst jedes Mal eine Meldung. Vertraglich vorher prüfen lassen.

**Preiserhöhung (Admin → Preise & Konditionen → „Preiserhöhung ankündigen“).** Prozentsatz, Stichtag (mindestens 30 Tage Frist) und optionaler Text; die Vorschau zeigt für jeden Kunden alt und neu. Nach „Jetzt ankündigen“ bekommt jeder Kunde eine Mail mit seinem persönlichen Link: Er kann zur Kenntnis nehmen oder einen Einwand schicken (du bekommst eine Meldung). Am Stichtag werden die monatlichen Preise der Buchungen und feste Positionen in Wartungsplänen automatisch angepasst; Kunden mit Einwand bleiben unverändert und stehen in der Detailansicht. Referenzkunden und Kunden mit laufender Kündigung sind ausgenommen.

**Rolle „Empfang“ und befristete Zugänge (Kunde → Team).** Empfang sieht nur Heute, Anfragen, Termine, Nachrichten, Kontakte und das eigene Konto, keine Rechnungen, Verträge, Kündigung, Datenexport oder Einstellungen der Website. Bei jedem Zugang kann der Inhaber ein Enddatum setzen („Zugang bis“): danach ist der Login gesperrt und laufende Sitzungen enden. Praktisch für Urlaubsvertretungen und Aushilfen.

## Verträge aus dem Portal senden

- **Referenzvertrag (Kunde):** Admin → Kunden → Kunde öffnen → Karte „Referenzvertrag“. Daten des Kunden sind vorausgefüllt, Projekt/Zeitraum ergänzen, dann „Erstellen und per Mail senden“ (oder „Nur erstellen“). Die Anlage 1 (was veröffentlicht werden darf) kreuzt der Kunde selbst an – es ist nichts vorangekreuzt. Der Kunde unterschreibt und schickt ihn zurück.
- **Handelsvertretervertrag (Vertriebler):** Admin → Vertrieb → Vertriebler öffnen → Karte „Handelsvertretervertrag“. Name und E-Mail sind vorausgefüllt; Rechtsform, Anschrift, Steuernummer, Haupt-/Nebenberuf und abweichende Provisionssätze optional eintragen. Anlage 3 füllt der Partner selbst aus.
- **Unterschriebene Fassung ablegen:** in der jeweiligen Karte „Unterschrieben ablegen“ (PDF/PNG/JPG, max. 6 MB, mit Datum). Beim Handelsvertretervertrag wird dadurch das Vereinbarungsdatum des Vertrieblers gesetzt.
- **Telefonleitfaden:** Vertriebler finden ihn im Vertriebsportal unter „Leitfaden“ (PDF öffnen/herunterladen). Nur für eingeloggte Vertriebler.

### Verträge online bestätigen, Erinnerungen, Übersicht

- **Online bestätigen:** Wurde ein Referenz- oder Handelsvertretervertrag per Mail gesendet, kann ihn der Empfänger auch direkt im Portal bestätigen (Kunde: Menü „Referenzvertrag“, Vertriebler: „Mein Vertrag“). Er trifft seine Auswahl bzw. trägt seine Angaben ein und bestätigt mit Name und Ort. Das Portal füllt das PDF aus, hängt eine Protokollseite an (Name, Konto, Zeitpunkt, IP, Prüfsumme), legt es ab und schickt dem Empfänger eine Kopie. Du bekommst eine Mail. Beim Handelsvertretervertrag wird das Vereinbarungsdatum gesetzt. Das ist eine einfache elektronische Signatur wie beim AVV; Markentrix‑Seite ist vorausgefüllt und gilt mit dem Versand als erklärt.
- **Erinnerungen:** Werktags prüft das Portal. Ist ein Vertrag nach 7 und nach 14 Tagen noch offen, bekommt der Empfänger eine freundliche Erinnerung (danach keine mehr), du eine Sammelmail.
- **Admin → Verträge:** Übersicht „Was fehlt noch?“ mit AVV, Referenzvertrag, Handelsvertretervertrag und Einarbeitung. Darunter die Referenzliste: Was hat welcher Kunde freigegeben (Elemente, Kanäle, Einschränkungen)? Nur das darf genutzt werden.
- **Widerruf:** Der Kunde kann die Freigabe im Portal widerrufen (du bekommst eine Mail, Inhalte innerhalb von 7 Tagen entfernen). Kam der Widerruf per Mail oder Telefon, vermerkst du ihn in der Referenzliste.
- **Einarbeitung:** Im Vertriebsportal steht auf „So geht’s“ und oben bei „Heute anrufen“ eine Checkliste (Vertrag, Leitfaden, Zwei-Faktor, IBAN, erster Anruf). Du siehst sie beim Vertriebler und in Admin → Verträge.
- **Leitfaden:** Unter „Leitfaden“ gibt es jetzt eine Suche im Text des Telefonleitfadens und den Knopf „Ich habe den Leitfaden gelesen“.

### Referenzseite, Zufriedenheit, Rangliste, Erinnerungen, Tipp im Monatsbericht

- **Gegenzeichnung:** Die Protokollseite eines online bestätigten Vertrags nennt jetzt auch, wann Markentrix den Vertrag versendet und damit seine Erklärung abgegeben hat.
- **Referenzseite (Admin → Verträge):** Die öffentliche Seite `/referenzen` zeigt nur, was Kunden für „Website von Markentrix“ freigegeben und mit Wortlaut angegeben haben (Kurzbeschreibung, Kennzahlen, Zitat, Link). Sie ist erst sichtbar, wenn du „Seite veröffentlichen“ einschaltest. Widerrufene Freigaben verschwinden sofort. Logos und Abbildungen fügst du bei Bedarf von Hand ein.
- **Zufriedenheit (Admin → Zufriedenheit):** Kunden werden 30 Tage nach dem Start und danach alle 90 Tage auf ihrer Startseite im Portal gefragt (0 bis 10). Eine Mail dazu gibt es nur, wenn der Kunde unter Einstellungen → „Meine Einwilligungen“ zugestimmt hat (Umfragen per Mail gelten als Werbung). Bei 0–6 bekommst du sofort eine Mail, bei 9–10 sieht der Kunde deinen Bewertungslink. Du siehst NPS, Verlauf und Kommentare.
- **Einwilligungen:** Der Kunde kann seine Zustimmung jederzeit im Portal widerrufen. Zustimmung und Widerruf werden mit Zeit und IP protokolliert.
- **Rangliste (Admin → Vertriebs-Auswertung):** Einschalten zeigt den Vertrieblern ihre Monatsplatzierung (Anrufe, Termine, Abschlüsse). Auf Wunsch mit Vornamen, sonst „Vertriebler 2“.
- **Nachfass-Erinnerung:** Werktags morgens bekommt jeder aktive Vertriebler eine Mail und eine Mitteilung mit den Leads, deren Wiedervorlage fällig ist oder bei denen seit einer Woche nichts passiert ist. Abschaltbar unter Konto.
- **Monatsbericht:** Enthält jetzt „Unser Tipp für den nächsten Monat“ (ein konkreter Vorschlag aus den Zahlen), im PDF und in der Mail.

## Vertrieb, Onboarding und Kundenportal: Neuerungen (Stand Oktober 2026)

**Vertrieb**
- *Sperrliste* (Admin → Vertrieb → Steuerung): Wer „kein Interesse“ sagt, widerspricht oder sich abmeldet, landet automatisch auf der Sperrliste (Mail, Telefon, Website-Domain). Beim Anlegen und Importieren wird abgewiesen, eingehende Anfragen werden trotzdem angenommen. Einträge lassen sich von Hand ergänzen oder entfernen. Die rechtliche Bewertung (Art. 14 DSGVO, UWG) klärt bitte der Anwalt.
- *Eingänge*: Neue Anfragen setzen den Lead auf „antwort“ mit Wiedervorlage heute. Automatische Verteilung an aktive Vertriebler ist **standardmäßig aus** (wegen der Provisionsansprüche), einschaltbar in der Steuerung. Dort stehen auch die Reaktionszeit für heiße Anfragen und die Sichtbarkeit der Paketpreise für Vertriebler (standardmäßig aus).
- *Ansprache-Grundlage* je Lead (Anfrage, Einwilligung, Firmenkontakt, Empfehlung, Bestandskontakt) und *Verlustgrund* bei „kein Interesse“ / „verloren“; die Auswertung zeigt die Gründe.
- *Angebot → Kunde*: Nimmt ein Interessent das Angebot an (Link oder Telefon), entsteht eine Aufgabe „Kunde anlegen“. Der Assistent „Zum Kunden machen“ legt Kunde, Paket, Buchung und Einladung in einem Schritt an. Angebotslinks bleiben bei Erinnerungen gültig; „neuer Link“ macht den alten ungültig.
- *Erstgespräch*: Vertriebler buchen freie Zeiten direkt im Lead (mit Zustimmung des Kunden), Erinnerungen 24 h und 2 h vorher.

**Onboarding**
- Wöchentliche Aufgaben für das Team: „Zugang prüfen, Einladung neu senden“ und nach 14 Tagen Stillstand „Kunde anrufen“. Kunden-Erinnerungen nennen jetzt auch Logo/Fotos, Zugänge und die Domain-Umstellung. Die Startkarte zeigt, wer gerade am Zug ist. Das Team bekommt eine Push-Meldung, wenn ein Kunde im Onboarding Unterlagen hochlädt.

**Kundenportal**
- Push-Meldungen bei neuen Freigaben und Team-Antworten, Freigaben mit Veröffentlichungsdatum und Bestätigungsschritt, Nachrichtenformular mit Anhang, Entwurfsspeicher und Doppelsend-Schutz, Fehlermeldungen als Einblendung statt Browser-Fenster, klarere Menünamen, Hilfe zur Domain-Umstellung unter „Website“.

**Betrieb**
- Bei Passwortwechsel enden alle anderen Sitzungen. Abstürzende Hintergrundjobs geben ihre Tagesmarke frei und lösen nach 10 Fehlern in Folge eine rote Ampel aus. Veröffentlichungsfehler lösen einen Alarm aus. Uploads werden auf Größe, Dateityp und Kunden-Kontingent (500 MB) geprüft. Nicht geändert: Upload-Grenzen je Datei und Offsite-Backup (braucht ein Ziel, z. B. Hetzner Storage Box), Image-Tags (`latest`) und `--forwarded-allow-ips`.

## Wissensbasis für den Assistenten (Kundenblatt → „Wissensbasis für den Assistenten“)
Hier pflegst du, was der KI-Assistent eines Kunden wissen darf. **Dateien hochladen** (TXT, MD oder PDF, bis 10 MB, mehrere auf einmal): Das Portal liest den Text und speichert ihn als Eintrag (Titel = Dateiname, Bereich frei wählbar, z. B. „preise“ oder „faq“). Die Datei selbst wird nicht aufbewahrt. Gescannte PDFs ohne Texterkennung, passwortgeschützte PDFs und Texte über 200.000 Zeichen werden mit einer verständlichen Meldung abgelehnt. Gleicher Titel im selben Bereich ersetzt den alten Eintrag. Einträge lassen sich ansehen, ändern, an- und ausschalten (nur „an“ nutzt der Assistent) und löschen. Zusätzlich kannst du Einträge von Hand schreiben. Nur für Admin.

**Kunde pflegt sein Wissen mit (Kundenportal → Mein Betrieb → „Mein Wissen für den Assistenten“, nur Inhaber):** Der Kunde sieht, was der Assistent weiß, und schlägt vor: neues Wissen (Text oder TXT/PDF-Datei), eine Änderung oder „nicht mehr nutzen“. Nichts wird sofort wirksam. Im Kundenblatt erscheint die Karte „Änderungswünsche des Kunden“ (zusätzlich eine Aufgabe und eine Push-Nachricht an dich). Mit **Übernehmen** gilt die Änderung, mit **Ablehnen** (optional mit Begründung) bekommt der Kunde die Antwort. Der Kunde kann offene Vorschläge zurückziehen.

**Gutschein-Erinnerung:** Ist eine Gutschein-Anfrage nach einem Tag noch offen (Zahlungslink oder Code fehlt), bekommt der Betrieb einmal eine Mail und eine Push-Nachricht. Derselbe Code lässt sich nicht an zwei Käufer senden.

## Hilfe-Suche und PDF-Anleitungen (Stand Oktober 2026)
- **Suchfeld „Hilfe“** oben in Vertriebs-, Kunden- und Admin-Portal. Eine Frage eintippen (z. B. „Leads anlegen“, „Wo trage ich meinen PayPal-Link ein?“) liefert die passende, auf das Portal zugeschnittene Anleitung mit Schritten und Menüweg.
- Nach jeder Anleitung fragt das Portal „Ist dein Problem damit gelöst?“. Bei **Nein** (mit kurzer Beschreibung) oder wenn keine Anleitung gefunden wurde („Frage an das Team senden“) bekommst du eine Mail (an die Firmen-Mailadresse aus Einstellungen → Firmendaten) und eine Karte **„Hilfe-Rückmeldungen“** auf der Admin-Übersicht, mit Knopf „Erledigt“. Die Karte zeigt auch, wie oft die Hilfe in 30 Tagen geholfen hat.
- **Artikel erweitern:** Dateien `portal/app/hilfe/vertrieb.json`, `kunde.json`, `admin.json` (Felder: `t` Titel, `k` Suchwörter, `wo` Menüweg, `s` Schritte, `n` Hinweise, `l` Link). Dieselben Dateien speisen die Suche **und** die PDF. Dort stehen auch Einleitung (`intro`), Einstieg (`start`) und `einstellungen`.
- **PDF-Anleitungen:** Vertriebler und Kunden bekommen die PDF automatisch als Anhang der Einladungs-Mail. Im Portal steht unter dem Suchfeld „Anleitung als PDF“ zum Herunterladen. Im Admin gibt es alle drei (Vertrieb, Kunden, Admin) zum Weitergeben.

## Kalender, Wochenplan, Stammkunden, Rollen, Warteliste (Stand Oktober 2026)
- **Wochenplan:** Zeiten je Wochentag mit Pausen (Betrieb und je Mitarbeiter), Urlaub/Sperrtage. Ohne Wochenplan gelten die alten einfachen Zeiten.
- **Branchen-Vorlagen** (Admin → Kunde → Buchungsvorlage): Friseur, Kfz, Fahrzeugpflege, Kosmetik, Handwerk, Fitness. Leistungen starten inaktiv und ohne Preis.
- **Kalender** im Kundenportal mit manuellen und wiederkehrenden Terminen, Gruppentermin (Personenzahl), **Stammkunden** mit Notizen.
- **Mitarbeiter-Zugang:** Team-Mitglieder lassen sich einem Kalender-Mitarbeiter zuordnen und sehen dann nur ihre Termine.
- **Weniger Ausfälle:** „Ich komme“-Link in der Erinnerung, **Warteliste** (bei Absage werden bis zu 3 Wartende benachrichtigt). SMS ist nicht gebaut.
- **Kunden-Ampel** und **Hilfe-Rückmeldungen** auf der Admin-Übersicht.
- **Vertrieb:** Übungsmodus (nichts wird gespeichert), Provisionssätze als Anzeige unter „Provisionen“. Mahnwesen automatisch ist standardmäßig aus.
- Datenbank-Migrationen 127 bis 129 laufen mit `install.sh`.

## Server härten, Rücknahme von Updates, automatische Tests (Stand Oktober 2026)
- `sudo mkctl haerten --status` zeigt den Sicherheitsstand (automatische Updates, fail2ban, SSH, Firewall, Neustart nötig). `sudo mkctl haerten --anwenden` richtet automatische Sicherheitsupdates (ohne automatischen Neustart) und fail2ban für SSH ein. `sudo mkctl haerten --firewall` schaltet die lokale Firewall (SSH, 80, 443) nach Rückfrage ein. Zusätzlich empfohlen: Hetzner-Firewall in der Cloud-Konsole. Der Selbsttest weist auf Neustart, fehlende Updates und fehlendes fail2ban hin (nur als Warnung).
- **Rücknahme:** `install.sh` hebt vor jedem Update den vorigen Programmstand auf (`/opt/markentrix/releases`, die letzten 5). `sudo mkctl rollback` setzt den Code auf den Stand davor zurück (mit Sicherung und Selbsttest), `mkctl rollback --liste` zeigt die Stände. Die Datenbank wird nicht zurückgesetzt; neue Tabellen bleiben und stören den alten Code nicht. Bei einem Datenproblem hilft die Wiederherstellung aus der Sicherung.
- **Automatische Tests:** `.github/workflows/tests.yml` führt bei jedem Push auf `server-paket` die Prüfungen aus (Shell-Skripte, pyflakes, danach der Volltest `tests/run.sh`). Ergebnis unter „Actions“ auf GitHub; rot heißt: nicht auf den Server einspielen.

## Wert-Karte, Vertriebler im Blick, Preislogik (Stand Oktober 2026)
- **Kundenportal → Heute:** Karte „Das hat Markentrix im <Monat> für dich getan“ mit Anfragen, automatischen Antworten, Terminen, erschienenen Kunden, Erinnerungen, Warteliste, Umsatz aus Terminen und erhaltenen Anzahlungen. Es erscheint nur, was es wirklich gab. Die Zeitersparnis ist eine gekennzeichnete Schätzung (3 Minuten je Vorgang, Wert `MINUTEN_JE_VORGANG` in `routes_wert.py`). Für den Empfang-Zugang ist die Karte nicht sichtbar.
- **Admin → Übersicht:** Karte „Vertriebler im Blick“ (Anrufe 7 Tage mit Vorwoche, Termine 30 Tage, Quote, offene Leads). Warnzeichen: keine Anrufe in 7 Tagen, Anrufe halbiert, Leads über 7 Tage unberührt, überfällige Wiedervorlagen, Leads über 14 Tage ohne Kontakt, viele Anrufe ohne Termine. Rot ab drei Warnzeichen.
- **`docs/PREISLOGIK.md`:** Entwurf zu Zusatzleistungen, Mitarbeiter-Grenzen, Laufzeit und Upgrade-Provision, mit Entscheidungsliste für dich.

## Pakete dazubuchen und Aktivität je Vertriebler (Stand Oktober 2026)
- **Kundenportal → Pakete & Zusatzleistungen** (nur Inhaber): Preisliste aus dem Katalog (`produkte`, `produkt_preise`, netto). „Dazubuchen“ legt eine Buchung mit Status `angefragt` und eingefrorenem Preis an, dazu Aufgabe, Mail an Admin und Kunde, Push. Pakete „auf Anfrage“ sind ein Angebotswunsch ohne Preis. Doppelbuchung ist gesperrt (409).
- **Referenzkunden** können ebenfalls dazubuchen: Preise 0 €, der reguläre Preis wird zur Info angezeigt (Regel wie bei `POST /api/admin/kunden/{id}/buchungen`).
- **Admin → Übersicht → „Neue Paketbuchungen“:** Bestätigen (Status `beauftragt`, Module werden freigeschaltet, Kunde bekommt Mail) oder Ablehnen. Nichts wird automatisch aktiv. Preisfragen und Provisionsfolgen: `docs/PREISLOGIK.md`.
- **Admin → Vertriebler → Karte „Aktivität“** (`GET /api/admin/vertrieb/partner/{id}/aktivitaet?tage=7|30|90`): Leads bearbeitet, Anrufe (erreicht), Termine, Notizen, aktive Tage, neue Leads/Kunden, Tagesbalken, letzte 25 Einträge. Erreichbar auch über den Namen in „Vertriebler im Blick“. Tests: t88, t89.
- **Nachlässe beim Dazubuchen** (Migration 130): Kombi Website + KI (ab BUSINESS) und Kombi Identität + Website je 500 € (Werte in `konditionen`), je Kunde einmal; Pilot-Nachlass 50 % auf die Einrichtung für die ersten 2 KI-Kunden (`pilot_plaetze_ki`, `pilot_nachlass_prozent`; 0 Plätze = aus). Abgezogen wird vom Projektpreis bzw. der Einrichtung, nie vom Monatspreis; der Grund steht in der Buchung und auf der Admin-Karte. Referenzkunden zahlen weiter 0 €. Prüfe bei „Bestätigen“, ob der Nachlass passt (z. B. wenn die andere Buchung später abgelehnt wird).
- **Neu buchbar (Preis auf Anfrage):** Website-Relaunch, Website-Pflege, SEO und GEO, Google-Unternehmensprofil. Preise trägst du im Admin unter Preise & Konditionen ein; dann sind sie direkt buchbar. Preisstand: 1. Oktober 2026. Werbebudget-Hinweis steht bei Leads/Anzeigen und oben auf der Seite.


## Website-Wachdienst: Fehler erklärt, www und Altlasten
- Zeigt die **Kunden-Ampel** „Website antwortet nicht richtig“, führt **Öffnen** zur Kundenseite. Ganz oben steht die Karte **Website-Problem** mit der genauen Fehlermeldung, der Ursache und den Lösungsschritten (z. B. fehlendes Zertifikat, DNS, Webserver, Website-API).
- „www.firma.de“ wird nicht extra überwacht, wenn „firma.de“ desselben Kunden überwacht wird. Websites bitte **ohne „www.“** anlegen (Admin lehnt „www.“ ab).
- Auf „offline“ gestellte Websites lösen keine Ampel und keinen Status mehr aus (alte Messwerte werden ignoriert).

## Angebote: Grund festhalten und Auswertung
- Beim Angebot (Lead-Karte oder Angebotsseite beim Kunden) gibt es **Grund festhalten**: Auswahl (zu teuer, Umfang, Zeitpunkt, Konkurrenz, kein Bedarf, interne Entscheidung, keine Antwort, sonstiges) plus kurze Anmerkung. Das geht bei gesendeten und abgelehnten Angeboten, nicht bei angenommenen.
- Lehnt der Empfänger online ab und wählt einen Grund, wird er automatisch übernommen. Beim Ablehnen durch das Team kann der Grund gleich mitgegeben werden.
- Die Karte **Angebote: Auswertung** zeigt „Woran Angebote scheitern“ nach Häufigkeit. Bei Leads steht der Grund außerdem im Verlauf.

## Angebot ohne Antwort: Erinnerung senden
- Gilt für Angebote an Leads und an bestehende Kunden, solange das Angebot „gesendet“ ist (nicht angenommen, nicht abgelehnt, nicht abgelaufen).
- Knopf **Erinnern** in „Angebote im Blick“ (Übersicht; erscheint, wenn die letzte Mail mindestens 3 Tage her ist), im Lead bei dem Angebot und auf der Angebotsseite beim Kunden.
- Es öffnet sich eine Vorschau mit Betreff und Text zum Ändern. Erst „Erinnerung jetzt senden“ verschickt die Mail, das Angebot hängt als PDF an. Von Hand geht nichts ohne deinen Klick raus.
- Drei Stufen: 1 freundliche Nachfrage, 2 Rückfrage, woran es liegt, dass noch nicht entschieden wurde (Preis, Umfang, Zeitpunkt, anderes Angebot), 3 letzte offene Nachfrage (ohne weitere Mails). Mehr als 3 Erinnerungen und Erinnerungen vor Ablauf von 3 Tagen sind gesperrt.
- Bei Leads bleibt der Online-Link gleich gültig, die Wiedervorlage springt auf 3 Tage später und im Lead steht ein Eintrag. Kunden-Angebote verweisen ins Kundenportal. Für Kunden-Angebote braucht ein Teil-Admin das Recht „Angebote, Rechnungen & Preise“. Leads, die sich von Mails abgemeldet haben, bekommen nichts.
- **Automatisch** (Einstellungen → „Angebote: automatisch erinnern“, Standard **aus**): Nach 3 Tagen ohne Antwort geht werktags ab 9 Uhr Erinnerung 1 raus, nach weiteren 3 Tagen Erinnerung 2. Die dritte schickst du selbst. Jede automatische Mail steht im Protokoll und im Lead.

## Fehler-Hilfe (Ursache und Lösungsvorschlag)
- Code: `portal/app/fehlerhilfe.py`. Eine Liste von Regeln (Muster, Ursache, Schritte, wer es behebt); die erste passende gewinnt, sonst kommt ein allgemeiner Hinweis. Neue Regel = ein Eintrag in `REGELN` plus ein Fall in `tests/t90.py`.
- Eingebunden an: unerwartete Fehler im Portal (Antwort nennt die Fehler-Nr.), abgestürzte Hintergrundjobs, Website-Protokoll beim Kunden (Zeile „Tipp: …“), Admin-Karte „Fehler-Hilfe“ in der Übersicht („Jetzt alles prüfen“ ohne Mailversand, „Fehler erklären“), Alarmliste unter Datenschutz & Qualität.
- Passwörter, Schlüssel und lange Zeichenketten werden vor dem Speichern entfernt. Gleiche Fehlerart wird je Quelle höchstens alle 30 Minuten (Jobs 60, Portal 10) neu gemeldet.

## Sicherheit: Schutz des Servers und der Pakete
- Der Root-Dienst (`bin/worker.py`) schreibt im Auftragsordner nie durch Symlinks. Ein Upload wird zuerst in `/srv/sites/.privat` (nur root) verschoben und erst dort geprüft. Neue Caddy-Dateien werden mit `caddy validate` geprüft und bei erkennbarem Fehler (z. B. doppelte Domain) nicht behalten.
- `install.sh` gibt veröffentlichte Website-Dateien nicht mehr an das Portal zurück (nur `live/` selbst und `angebote/`).
- Einzeln gesperrte Zugänge bleiben auch nach „Kunde pausiert → aktiv“ gesperrt.
- GitHub prüft wöchentlich die Python-Pakete (`pip-audit`) und das Repository auf versehentliche Schlüssel (gitleaks); Dependabot schlägt Updates vor. Meldet die Prüfung ein Paket: Version in `portal/requirements.txt` anheben, `bash tests/run.sh`, dann `mkctl update`.

## Mails im Namen des Kunden (Layout, Logo, Signatur)
- Alle Mails, die über die Website-Dienste im Namen eines Kunden verschickt werden (Eingangsbestätigung, Terminbestätigung, Absage, Erinnerung, Anfragen ans Team), kommen als HTML-Mail: Kopf mit Logo (oder Firmenname) in der Markenfarbe, Angaben als Tabelle, Absage/Bezahlen als Knopf, Signatur. Die Textfassung bleibt als Alternative erhalten.
- **Logo und Farbe:** Admin → Kunden → (Kunde) → Branding (PNG oder JPG, bis 400 KB; SVG zeigen Mail-Programme nicht). Das Logo erscheint auch auf der Absage-Seite.
- **Signatur:** Der Kunde stellt sie unter Website-Dienste → Kontaktformular ein („Vorschlag aus meinen Firmendaten einfügen“). Leer = „Mit freundlichen Grüßen“ und Firmenname. Der Knopf „Testmail senden“ zeigt das Ergebnis.
- Beschriftungen der Formularfelder kommen aus der Website (`name`-Feld) bzw. aus der Liste in `routes_siteapi.py` (`LABELS`); fehlt eine, steht der Feldname.

## Fotos von Besuchern mit Löschfrist (Stand Oktober 2026)
- Kundenportal → Website-Dienste → **Fotos von Besuchern**: Schalter (Standard **aus**) und **Löschfrist** (Standard 90 Tage, 7 bis 365). Die Frist gilt für neue Fotos, vorhandene behalten ihr Datum.
- Besucher laden bis zu 5 Fotos (JPG, PNG, WebP) im Kontaktformular, in der Terminbuchung (Baustein `site.js`) oder über die Website-API (`/api/foto`, Feld `fotos` bei `/api/anfrage`, siehe `docs/WEBSITE-API.md`). Der Besucher sieht beim Hochladen, nach wie vielen Tagen die Fotos gelöscht werden.
- Das Portal prüft den Bildinhalt, entfernt Standort und Kameradaten, speichert das Foto in der Datenbank (`website_fotos`, nur für den eigenen Betrieb lesbar) und zeigt es bei Anfragen, Terminen und Buchungen. Zusätzlich hängt es an der Mail an den Betrieb (bis 8 MB zusammen).
- **Löschen:** Der Betrieb kann jedes Foto selbst löschen. Der Hintergrunddienst löscht abgelaufene Fotos und nie abgeschickte Uploads (nach 24 Stunden) und schreibt beides ins Löschprotokoll. Mit einer gelöschten Anfrage verschwinden ihre Fotos. Speichergrenze je Betrieb: 200 MB.
- Der Datenexport bei Vertragsende enthält die Fotos (Ordner `fotos/`), die Löschung bei Offboarding entfernt sie.
- Rechtlich: Hinweis in der Datenschutzerklärung des Betriebs nötig, Punkt steht in `docs/ANWALT-CHECKLISTE.md`.
