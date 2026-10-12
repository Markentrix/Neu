# Noch benötigte Asset-Dateien — Markentrix

Stand: 14.08.2026. Rein technische Liste (keine Rechtsfragen, siehe dafür `LEGAL_INPUTS_REQUIRED.md`).

## Schriftdateien — erledigt
Space Grotesk (600/700, 800 als Bold-Ersatz da Space Grotesk kein 800 führt) und Inter (300/400/500/600 + 300-italic) liegen als `.ttf` in `fonts/` und sind in `fonts/fonts.css` per `url()` eingebunden (SIL Open Font License, siehe `uploads/Space_Grotesk/OFL.txt` und `uploads/Inter/OFL.txt`). Optional später: zu `.woff2` konvertieren für kleinere Dateigröße — funktional aber bereits vollständig.

## Hero-Video (aktuell: deaktiviert, `_initHeroVideo()` entfernt das `<video>`-Element vor jedem Request)
Quelldatei: `videos/markentrix_hero_background.webm` (~4,6 MB) — bleibt unangetastet im Projekt.
Für die Reaktivierung: extern komprimieren auf < 1,5 MB (WebM VP9 oder AV1, ca. 1280×720, kurzer Loop ohne Ton, z. B. `ffmpeg -i quelle.mov -vf scale=1280:-2 -t 12 -an -c:v libvpx-vp9 -b:v 700k -crf 36 -row-mt 1 hero.webm`), Posterbild als AVIF/WebP ergänzen, danach die alte Lade-/Play-Logik in `_initHeroVideo()` wiederherstellen.

## Externes Kundenportal
Kundenlogin verweist jetzt auf `https://markentrix.netlify.app/`. Bitte prüfen, ob dieses Portal erreichbar ist und eigene Impressum-/Datenschutzseiten besitzt (in diesem Projekt nicht einsehbar/veränderbar).
