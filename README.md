# Neu – Higgsfield über die API

Dieses Repo enthält ein kleines Python-Modul, mit dem Claude (oder du selbst)
Bilder und Videos direkt über die Higgsfield-API erzeugt. Die API wird
pay-as-you-go aus einem Dollar-Guthaben bezahlt und braucht kein Website-Abo.

## Voraussetzungen

* Python 3.10 oder neuer, `pip install -r requirements.txt`
* API-Key aus https://console.higgsfield.ai (Key-ID und Secret)
* Zugangsdaten hinterlegen:
  * **Claude-Cloud-Umgebung:** als Network secret für `api.higgsfield.ai`
    mit Header `Authorization`, Präfix `Key`, Wert `ID:SECRET`. Der Proxy
    hängt den Header selbst an, im Code ist nichts zu setzen.
  * **Lokal:** `export HF_KEY="ID:SECRET"` (oder `HF_API_KEY` und
    `HF_API_SECRET`). Nie in Dateien im Repo schreiben.

## Befehle

```bash
python -m higgsfield_api check                       # kostenloser Verbindungstest
python -m higgsfield_api models                      # Modelle und Listenpreise
python -m higgsfield_api estimate hailuo-t2v --duration 10
python -m higgsfield_api video hailuo-t2v "Prompt" --duration 6 --name clip1
python -m higgsfield_api video kling-std-i2v "Prompt" --image ./start.jpg
python -m higgsfield_api image soul "Prompt" --aspect 9:16 --resolution 2K
python -m higgsfield_api status <request_id> --download
```

`--dry-run` zeigt nur Schätzung und Request-Body, ohne etwas zu senden.
Fertige Dateien landen in `output/`. Higgsfield hält Ausgaben nur
mindestens sieben Tage vor, deshalb werden sie sofort heruntergeladen.

## Aus Python

```python
from higgsfield_api import HiggsfieldClient, estimate_cost

c = HiggsfieldClient()
print(estimate_cost("kling-std-i2v", {"duration": 5}))
url = c.upload("start.jpg")
result = c.generate("kling-std-i2v", prompt="sanfte Kamerafahrt", image_url=url, duration=5)
print(result["files"])
```

## Modelle

| Kurzname | Pfad | Einheit | Listenpreis |
|---|---|---|---|
| hailuo-t2v | /minimax/hailuo-2.3/standard/text-to-video | Sekunde | 0,0467 USD |
| hailuo-i2v | /minimax/hailuo-2.3/standard/image-to-video | Sekunde | 0,0467 USD |
| kling-std-i2v | /kling-video/v2.5-turbo/standard/image-to-video | Sekunde | 0,042 USD |
| kling-pro-i2v | /kling-video/v2.5-turbo/pro/image-to-video | Sekunde | 0,042 USD |
| kling-pro-t2v | /kling-video/v2.5-turbo/pro/text-to-video | Sekunde | 0,042 USD |
| soul | /higgsfield-ai/soul/standard | Bild | 0,0938 USD |

Weitere Modelle: Pfad und Parameter aus https://docs.higgsfield.ai entnehmen
und in `higgsfield_api/models.py` eintragen. Die Preise sind Listenpreise,
Kontorabatte liegen meist bei 15 bis 50 Prozent. Verbindlich ist die
Abrechnung in der Konsole.

## Kosten und Fehler

* Es gibt keinen dokumentierten Estimate-Endpunkt. Die Schätzung rechnet
  lokal mit Dauer mal Listenpreis und ist eine Obergrenze.
* Fehlgeschlagene oder als NSFW markierte Jobs werden nicht berechnet.
* HTTP 403 bedeutet: Guthaben leer, in der Konsole aufladen.
* Jeder Submit trägt einen `Idempotency-Key`, Wiederholungen nach
  Netzfehlern erzeugen keinen doppelten Job.
