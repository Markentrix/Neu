<?php
/**
 * Markentrix · gemeinsame E-Mail-Vorlage (HTML im Markentrix-Design, nur Funktionen, keine Ausgabe).
 * Wird von anfrage.php eingebunden. Caddy führt nur die freigegebenen Endpunkte aus, diese Datei ist von außen nicht aufrufbar.
 *
 * Farben aus der Corporate Identity: Graphite Navy #0C2128, Cyan #045268, Blue #045268, Violet (Akzent) #045268,
 * helle Flächen #F7F4EE und #F7F4EE. Alle Stile stehen inline (E-Mail-Programme ignorieren meist <style>), Layout mit Tabellen.
 */
declare(strict_types=1);

function mx_h(string $s): string {
  return htmlspecialchars($s, ENT_QUOTES, 'UTF-8');
}

/** Rahmen (Markenhandbuch 3.0): heller Kopf mit Logo und Kennzeichen, Kupferlinie, weißer Inhalt, Kreide-Fuß. $inner enthält fertiges HTML. */
function mx_shell(string $tag, string $inner, string $footer, string $preheader = ''): string {
  return '<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"></head>'
    . '<body style="margin:0;padding:0;background:#F7F4EE;font-family:Arial,Helvetica,sans-serif;color:#0C2128;-webkit-text-size-adjust:100%">'
    . '<div style="display:none;max-height:0;overflow:hidden;opacity:0;font-size:1px;line-height:1px;color:#F7F4EE">' . mx_h($preheader) . '</div>'
    . '<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:20px 10px">'
    . '<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;background:#FFFFFF;border-radius:8px;overflow:hidden">'
    . '<tr><td style="background:#FFFFFF;padding:20px 26px;border-bottom:1px solid #EAE2D3"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
    . '<td><img src="https://markentrix.de/img/logo/markentrix-logo-farbe-hell.png" width="160" height="26" alt="Markentrix" style="display:block;border:0;width:160px;height:auto"></td>'
    . '<td align="right" style="color:#045268;font-size:12px;letter-spacing:.09em;font-weight:bold;text-transform:uppercase">' . mx_h($tag) . '</td></tr></table></td></tr>'
    . '<tr><td style="height:3px;background:#C67432;font-size:0;line-height:3px">&nbsp;</td></tr>'
    . $inner
    . '<tr><td style="background:#F7F4EE;border-top:1px solid #E1F0F6;padding:16px 26px;font-size:12px;line-height:1.6;color:#4E5C5F">' . $footer . '</td></tr>'
    . '</table></td></tr></table></body></html>';
}

/** Überschrift-Block mit kleinem Kennzeichen (Eyebrow) in Pfauenblau. */
function mx_title(string $eyebrow, string $title, string $sub = ''): string {
  return '<tr><td style="padding:26px 26px 6px"><p style="margin:0 0 6px;font-size:12px;color:#045268;letter-spacing:.1em;text-transform:uppercase;font-weight:bold">' . mx_h($eyebrow) . '</p>'
    . '<h1 style="margin:0;font-size:24px;line-height:1.25;color:#0C2128;word-break:break-word">' . mx_h($title) . '</h1>'
    . ($sub !== '' ? '<p style="margin:8px 0 0;font-size:14px;line-height:1.5;color:#4E5C5F">' . $sub . '</p>' : '') . '</td></tr>';
}

/** Abschnitt mit Zwischenüberschrift. $html ist fertiges HTML. */
function mx_section(string $heading, string $html): string {
  return '<tr><td style="padding:14px 26px 4px"><p style="margin:0 0 8px;font-size:13px;font-weight:bold;color:#0C2128;text-transform:uppercase;letter-spacing:.06em">' . mx_h($heading) . '</p>' . $html . '</td></tr>';
}

/** Tabelle mit Bezeichnung links und Wert rechts. $rows: [[label, valueHtml], …]; leere Werte entfallen. */
function mx_rows(array $rows): string {
  $out = '';
  foreach ($rows as [$l, $v]) {
    if ($v === '' || $v === null) continue;
    $out .= '<tr><td valign="top" style="width:130px;padding:8px 12px 8px 0;border-bottom:1px solid #E1F0F6;font-size:13px;color:#4E5C5F">' . mx_h((string) $l) . '</td>'
          . '<td valign="top" style="padding:8px 0;border-bottom:1px solid #E1F0F6;font-size:14px;line-height:1.5;color:#0C2128;word-break:break-word">' . $v . '</td></tr>';
  }
  return $out === '' ? '' : '<table role="presentation" width="100%" cellpadding="0" cellspacing="0">' . $out . '</table>';
}

/** Hervorgehobener Textkasten (z. B. Nachricht). Zeilenumbrüche bleiben erhalten. */
function mx_quote(string $text): string {
  return '<div style="background:#F7F4EE;border:1px solid #E1F0F6;border-left:4px solid #045268;border-radius:8px;padding:12px 14px;font-size:14px;line-height:1.6;color:#0C2128;word-break:break-word">'
    . nl2br(mx_h($text), false) . '</div>';
}

/** Schaltfläche (primär: Cyan-Blau, sekundär: weiß mit Rand). */
function mx_btn(string $href, string $label, bool $primary = true): string {
  $style = $primary
    ? 'background:#045268;color:#0C2128;border:1px solid #045268'
    : 'background:#FFFFFF;color:#0C2128;border:1px solid #62B2D0';
  return '<a href="' . mx_h($href) . '" style="display:inline-block;margin:0 8px 8px 0;' . $style . ';font-weight:bold;font-size:14px;text-decoration:none;padding:11px 20px;border-radius:10px">' . mx_h($label) . '</a>';
}

/** Kleines Kennzeichen (Chip). */
function mx_chip(string $text, string $bg = '#F7F4EE', string $fg = '#045268'): string {
  return '<span style="display:inline-block;background:' . $bg . ';color:' . $fg . ';font-size:12px;font-weight:bold;padding:4px 10px;border-radius:20px">' . mx_h($text) . '</span>';
}

/** Nummerierte Schritte (Kreis mit Zahl). $steps: [[Titel, Text], …] */
function mx_steps(array $steps): string {
  $out = '<table role="presentation" width="100%" cellpadding="0" cellspacing="0">';
  foreach ($steps as $i => [$t, $d]) {
    $out .= '<tr><td valign="top" style="width:40px;padding:0 0 12px"><div style="width:28px;height:28px;line-height:28px;border-radius:8px;background:#0C2128;color:#FFFFFF;text-align:center;font-size:13px;font-weight:bold">' . ($i + 1) . '</div></td>'
          . '<td valign="top" style="padding:0 0 12px;font-size:14px;line-height:1.5"><b style="color:#0C2128">' . mx_h($t) . '</b><br><span style="color:#4E5C5F">' . mx_h($d) . '</span></td></tr>';
  }
  return $out . '</table>';
}

/** Text und HTML zu einer multipart/alternative-Nachricht zusammensetzen. Gibt [Body, Content-Type-Header] zurück. */
function mx_multipart(string $text, string $html): array {
  $b = 'mx' . bin2hex(random_bytes(8));
  $body = "--$b\nContent-Type: text/plain; charset=UTF-8\nContent-Transfer-Encoding: base64\n\n" . rtrim(chunk_split(base64_encode($text), 76, "\n")) . "\n"
        . "--$b\nContent-Type: text/html; charset=UTF-8\nContent-Transfer-Encoding: base64\n\n" . rtrim(chunk_split(base64_encode($html), 76, "\n")) . "\n--$b--\n";
  return [$body, 'Content-Type: multipart/alternative; boundary="' . $b . '"'];
}
