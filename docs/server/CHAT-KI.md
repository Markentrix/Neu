# KI-Chat einschalten (Stand 31.10.2026)

Der Chat auf markentrix.de hat zwei Modi. **Ohne Schlüssel** antwortet er mit vorgefertigten Antworten aus der FAQ (keine KI, keine Kosten). **Mit Schlüssel** antwortet eine KI, aber nur anhand der Wissensbasis der Website. Fehlt der Schlüssel oder fällt der Dienst aus, springt der Chat automatisch auf die vorgefertigten Antworten zurück.

## 1. Zugang beim Anbieter holen
- **Anthropic (Claude):** console.anthropic.com → API Keys → neuen Schlüssel anlegen. Unter „Limits“ ein **monatliches Ausgabenlimit** setzen (z. B. 20 €).
- **OpenAI:** platform.openai.com → API keys → neuen Schlüssel anlegen. Unter „Limits“ ein **monatliches Budget** setzen.
- Den Schlüssel nie in den Chat, in Mails oder ins Repository schreiben. Er gehört nur auf den Server.
- Auftragsverarbeitung: Beim Anbieter die Datenverarbeitungsvereinbarung (DPA) annehmen (steht in den Einstellungen bzw. den Geschäftsbedingungen). API-Eingaben werden laut Anbieterbedingungen nicht zum Training verwendet; bitte in den Einstellungen prüfen.

## 2. Auf dem Server eintragen
1. In `/opt/neu/server/.env` ergänzen (Anthropic):
   ```
   MX_AI_KEY=sk-...
   MX_AI_PROVIDER=anthropic
   ```
   Für OpenAI `MX_AI_PROVIDER=openai`. Das Modell steht im Standard auf `claude-haiku-5-5` (Anthropic) bzw. `gpt-4o-mini` (OpenAI); ein anderes Modell mit `MX_AI_MODEL=…` ergänzen.
2. Neue `docker-compose.yml` und `markentrix-site.caddy` aus `docs/server/` einspielen (sie reichen die Variablen durch und erlauben `/api/chat.php`).
3. Neu starten: `docker compose up -d` im Ordner mit der compose-Datei, danach Caddy neu laden.
4. Die ZIP der Website einspielen (enthält `api/chat.php` und das neue Chat-Skript).

## 3. Prüfen
```
curl -s https://markentrix.de/api/chat.php?status=1                       # erwartet {"ok":true,"enabled":true}
curl -s -XPOST https://markentrix.de/api/chat.php -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"Was kostet eine Website?"}]}'  # erwartet "ok":true und eine Antwort
```
Dann auf der Website den Knopf „Fragen?“ öffnen, „Einverstanden, mit KI chatten“ wählen und einige Fragen stellen, auch eine Frage, die nicht in der Wissensbasis steht (der Assistent muss das zugeben und das Frageformular anbieten).

## 4. Schutz und Kosten
- Pro IP höchstens 15 Nachrichten in 10 Minuten und 80 pro Tag, insgesamt `MX_AI_DAILY_MAX` Antworten pro Tag (Standard 400). Danach antwortet der Chat ohne KI.
- Antwort höchstens 400 Token, Eingabe höchstens 300 Zeichen, die letzten 6 Nachrichten gehen mit. Der Systemtext mit der Wissensbasis (rund 3.000 Token) wird beim Anbieter zwischengespeichert, soweit er das unterstützt.
- Grobe Größenordnung: Eine Antwort kostet bei einem kleinen Modell im Bereich von Bruchteilen eines Cents; 400 Antworten am Tag liegen damit meist im niedrigen einstelligen Euro-Bereich pro Monat. Verbindlich sind die Preise des Anbieters.
- Absicherung der Antworten: Eurobeträge und Prozentangaben, die nicht in der Wissensbasis stehen, werden nicht ausgeliefert (der Besucher bekommt stattdessen den Hinweis, direkt nachzufragen). Fremde Internetadressen werden entfernt, Gedankenstriche ersetzt.
- Nachrichtentexte werden weder gespeichert noch protokolliert.
- Notbremse: `MX_AI_ENABLED=0` in der compose-Datei oder Schlüssel entfernen, Container neu starten. Der Chat läuft sofort ohne KI weiter.

## 5. Wissensbasis pflegen
Die Wissensbasis entsteht beim Bauen der Website aus der FAQ-Seite (`src/pages/faq.html`) und den Handtexten in `src/chat-extra.json`. Neue Antworten dort eintragen, bauen, hochladen: Die KI kennt sie ab dann. Preise und Fristen nie nur im Chat ändern, immer in der Quelle.

## 6. Recht
Die Datenschutzerklärung (Abschnitte 5c und 14) beschreibt den KI-Chat. Vor dem Einschalten prüfen: Anbieter in Abschnitt 14 stimmt mit dem eingesetzten überein, DPA ist angenommen, die Hinweistexte im Chat („Sie schreiben mit einer KI“, Einwilligung vor dem ersten Gespräch) sind gewollt. Rechtliche Prüfung bleibt bei Ihnen oder Ihrer Beratung.
