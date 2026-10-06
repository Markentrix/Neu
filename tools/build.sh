#!/usr/bin/env bash
# Erzeugt die minimierten Produktiv-Dateien. Nach jeder Änderung an styles.css / app.js ausführen:  bash tools/build.sh
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tools/events.py
npx -y esbuild app.js --minify --target=es2019 --outfile=app.min.js --log-level=warning
npx -y esbuild styles.css --minify --outfile=styles.min.css --log-level=warning
python3 - <<'PY'
import re
css=open('fonts/fonts.css').read()+open('styles.min.css').read()
css=re.sub(r'/\*.*?\*/','',css,flags=re.S).replace('\n','')
css=css.replace('url(monoton','url(fonts/monoton').replace('url(outfit','url(fonts/outfit').replace('url(spacegrotesk','url(fonts/spacegrotesk')
h=open('index.html',encoding='utf8').read()
block='<!--css--><style>'+css+'</style><!--/css-->'
if '<!--css-->' in h:
    h=re.sub(r'<!--css-->.*?<!--/css-->',lambda m:block,h,flags=re.S)
else:
    h=h.replace('<link rel="stylesheet" href="fonts/fonts.css">\n<link rel="stylesheet" href="styles.css">',block)
h=h.replace('<script src="app.js" defer>','<script src="app.min.js" defer>')
open('index.html','w',encoding='utf8').write(h)
for f in ['impressum.html','datenschutz.html','404.html']:
    x=open(f,encoding='utf8').read().replace('href="styles.css"','href="styles.min.css"').replace('href="/styles.css"','href="/styles.min.css"')
    open(f,'w',encoding='utf8').write(x)
PY
echo "build ok"
