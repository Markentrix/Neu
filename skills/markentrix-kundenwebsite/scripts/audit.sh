#!/usr/bin/env bash
# Statischer Audit für Markentrix-Websites. Nutzung: bash audit.sh <ordner>
# Findet typische Verstöße gegen Datenschutz, Barrierefreiheit, Performance. Ersetzt weder Lighthouse noch manuellen Test.
dir="${1:-.}"; fail=0; warn=0
F(){ echo "FAIL  $*"; fail=$((fail+1)); }
W(){ echo "WARN  $*"; warn=$((warn+1)); }
mapfile -t html < <(find "$dir" -name '*.html' -not -path '*/node_modules/*')
[ ${#html[@]} -eq 0 ] && { echo "Keine HTML-Dateien in $dir"; exit 2; }
srcs=$(find "$dir" \( -name '*.html' -o -name '*.css' -o -name '*.js' \) -not -path '*/node_modules/*')

# Datenschutz: Drittanbieter / Tracking
if grep -InE 'fonts\.(googleapis|gstatic)\.com|cdnjs\.|cdn\.jsdelivr|unpkg\.com|ajax\.googleapis|code\.jquery\.com' $srcs; then F "CDN/Google Fonts: alles selbst hosten"; fi
if grep -InE 'googletagmanager|google-analytics|connect\.facebook\.net|fbq\(|gtag\(|hotjar|analytics\.tiktok|clarity\.ms' $srcs; then F "Tracking-Code gefunden: nur nach Consent laden"; fi
if grep -InE 'youtube\.com/embed|google\.com/maps|player\.vimeo' $srcs; then W "Drittanbieter-Embed: Zwei-Klick-Lösung nötig"; fi
if grep -InE '<(script|link|img|iframe)[^>]+(src|href)="https?://' "${html[@]}" | grep -v 'canonical\|og:' ; then W "Externe Ressourcen eingebunden"; fi

for f in "${html[@]}"; do
  grep -q '<html[^>]*lang=' "$f" || F "$f: lang-Attribut fehlt"
  grep -q '<title>[^<]\+' "$f" || F "$f: <title> fehlt"
  grep -q 'name="description"' "$f" || W "$f: Meta-Description fehlt"
  grep -q 'name="viewport"' "$f" || F "$f: Viewport-Meta fehlt"
  n=$(grep -o '<h1[ >]' "$f" | wc -l); [ "$n" -eq 1 ] || W "$f: $n <h1> (erwartet 1)"
  grep -q '<main' "$f" || F "$f: <main> fehlt"
  grep -qi 'class="skip\|skip-link\|Zum Inhalt' "$f" || W "$f: Skip-Link fehlt"
  grep -oE '<img[^>]*>' "$f" | while read -r t; do
    echo "$t" | grep -q 'alt=' || echo "FAIL  $f: <img> ohne alt: $t"
  done | tee /dev/stderr | grep -q FAIL && fail=$((fail+1))
  grep -oE '<img[^>]*>' "$f" | grep -vq 'width=' && W "$f: <img> ohne width/height (CLS)"
  grep -q 'impressum' "$f" || W "$f: kein Impressum-Link"
  grep -q 'datenschutz' "$f" || W "$f: kein Datenschutz-Link"
  grep -q 'PLATZHALTER' "$f" && W "$f: Platzhalter noch vorhanden (nicht live!)"
  if grep -q 'data-demo' "$f"; then grep -qi 'noindex' "$f" || F "$f: Demo ohne noindex"; W "$f: Demo-Modus aktiv (vor Livegang entfernen)"; else grep -qi 'name="robots"[^>]*noindex' "$f" && W "$f: noindex aktiv (nur Staging/Demo)"; fi
  grep -qE 'tabindex="[1-9]' "$f" && F "$f: positives tabindex"
  grep -qE 'href="#"' "$f" && W "$f: leerer Link href=\"#\""
  grep -qE 'target="_blank"' "$f" && ! grep -q 'noopener' "$f" && W "$f: target=_blank ohne rel=noopener"
  grep -qE '<input[^>]*type="checkbox"[^>]*checked' "$f" && F "$f: vorangekreuzte Checkbox"
done

css=$(find "$dir" -name '*.css' -not -path '*/node_modules/*')
[ -z "$css" ] && css=/dev/null
grep -qE 'prefers-reduced-motion' $css || F "prefers-reduced-motion fehlt im CSS"
grep -qE 'font-display' $css || W "font-display nicht gesetzt"
grep -InE 'transition:\s*all|animation:[^;]*(width|height|top|left|margin)' $css && W "Layout-Animation/transition: all vermeiden"
grep -InE 'outline:\s*(none|0)' $css | grep -v focus-visible && W "outline entfernt: Fokus sichtbar halten"

# Gewicht
big=$(find "$dir" -type f \( -name '*.jpg' -o -name '*.jpeg' -o -name '*.png' -o -name '*.webp' -o -name '*.avif' \) -size +200k)
[ -n "$big" ] && W "Bilder > 200 KB: $big"
js=$(find "$dir" -name '*.js' -not -path '*/node_modules/*' -exec cat {} + </dev/null | gzip -c | wc -c); [ "$js" -gt 61440 ] && W "JS gzip $js B > 60 KB"
for p in robots.txt sitemap.xml; do [ -f "$dir/$p" ] || W "$p fehlt"; done

echo "---"; echo "Ergebnis: $fail FAIL, $warn WARN"; [ "$fail" -eq 0 ]
