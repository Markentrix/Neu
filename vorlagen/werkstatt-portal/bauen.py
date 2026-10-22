#!/usr/bin/env python3
"""Erzeugt vorlagen/werkstatt-portal/website-fertig/ (portalfähige Kundenvorlage nach dem Skill "Website mit Portal")
und die Vorschau-Kopie static/beispiel/werkstatt-portal/ (mit simulierten Schnittstellen). Aufruf: python3 vorlagen/werkstatt-portal/bauen.py"""
import os, shutil, re
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'vorlagen', 'werkstatt-portal', 'website-fertig')
PREV = os.path.join(ROOT, 'static', 'beispiel', 'werkstatt-portal')
SRC_IMG = os.path.join(ROOT, 'static', 'beispiel', 'werkstatt-muster', 'img')
FONTS = os.path.join(ROOT, 'static', 'fonts')
TEL, TELHREF = '05141&nbsp;00&nbsp;00&nbsp;03', 'tel:+495141000003'
MAIL = 'kontakt@werkstatt-muster.example'

def w(path, text):
    p = os.path.join(OUT, path); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(text)

SPRITE = '''<svg class="sprite" width="0" height="0" focusable="false" aria-hidden="true"><defs>
  <symbol id="w-phone" viewBox="0 0 24 24"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8.1 9.7a16 16 0 0 0 6 6l1.2-1.2a2 2 0 0 1 2.1-.5c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/></symbol>
  <symbol id="w-wrench" viewBox="0 0 24 24"><path d="M14.7 6.3a4 4 0 0 0-5.4 5l-6.2 6.2a2 2 0 0 0 2.8 2.8l6.2-6.2a4 4 0 0 0 5-5.4l-2.5 2.5-2.1-.4-.4-2.1z"/></symbol>
  <symbol id="w-tire" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/><path d="M12 3v6M12 15v6M3 12h6M15 12h6"/></symbol>
  <symbol id="w-brake" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="2.5"/><path d="M5 5l3 3M19 5l-3 3M5 19l3-3M19 19l-3-3"/></symbol>
  <symbol id="w-snow" viewBox="0 0 24 24"><path d="M12 2v20M4.2 7l15.6 10M19.8 7L4.2 17"/><path d="M9.5 3.5L12 6l2.5-2.5M9.5 20.5L12 18l2.5 2.5"/></symbol>
  <symbol id="w-clip" viewBox="0 0 24 24"><rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4h6v3H9zM9 12h6M9 16h4"/></symbol>
  <symbol id="w-spark" viewBox="0 0 24 24"><path d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/><path d="M18 16l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z"/></symbol>
  <symbol id="w-pin" viewBox="0 0 24 24"><path d="M12 22s7-6.2 7-12a7 7 0 0 0-14 0c0 5.8 7 12 7 12z"/><circle cx="12" cy="10" r="2.5"/></symbol>
</defs></svg>'''

def head(title, desc, extra=''):
    return f'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="robots" content="noindex, nofollow">
<link rel="icon" href="favicon.ico" sizes="32x32">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/fonts/fonts.css">
<link rel="stylesheet" href="assets/style.css">
{extra}</head>
<body>
{SPRITE}
<header class="top">
  <a class="logo" href="index.html"><span class="mark" aria-hidden="true">WM</span>Werkstatt Muster</a>
  <nav class="nav" aria-label="Hauptnavigation">
    <a href="index.html#leistungen">Leistungen</a><a href="index.html#ablauf">Ablauf</a><a href="index.html#zeiten">Zeiten und Anfahrt</a><a href="index.html#faq">Fragen</a>
  </nav>
  <a class="btn btn-call" href="{TELHREF}"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#w-phone"/></svg>{TEL}</a>
</header>
'''

FOOT = f'''<footer class="foot">
  <div class="wrap">
    <p><b>Werkstatt Muster</b> · Musterstraße 3 · 29221 Celle · <a href="{TELHREF}">05141 00 00 03</a> · <a href="mailto:{MAIL}">{MAIL}</a></p>
    <p><a href="impressum.html">Impressum</a> · <a href="datenschutz.html">Datenschutz</a> · <span data-mk="cookies"></span></p>
    <p class="foot-note">Fiktiver Beispielbetrieb. Bildmotive mit KI-Unterstützung erstellt, sie dienen als Symbolbilder und zeigen keinen echten Betrieb.</p>
  </div>
</footer>
<script src="assets/app.js" defer></script>
</body>
</html>
'''

def img(n, alt, sizes, lazy=True, cls=''):
    ld = 'loading="lazy" decoding="async"' if lazy else 'fetchpriority="high" decoding="async"'
    c = f' class="{cls}"' if cls else ''
    return (f'<img{c} src="assets/img/{n}-800.webp" srcset="assets/img/{n}-800.webp 800w, assets/img/{n}-1400.webp 1400w" sizes="{sizes}" '
            f'width="1400" height="1050" alt="{alt}" {ld}>')

FALLBACK = f'''<div class="fallback" id="api-fallback" hidden role="status">
  <b>Die Online-Terminanfrage ist gerade nicht erreichbar.</b>
  <span>Sie erreichen uns direkt: <a href="{TELHREF}">05141 00 00 03</a>, per <a href="https://wa.me/495141000003" rel="noopener">WhatsApp</a> oder per <a href="mailto:{MAIL}">E-Mail</a>.</span>
</div>'''

INDEX = head('Autowerkstatt Celle: Inspektion, Reifen, Bremsen',
  'Autowerkstatt Werkstatt Muster in Celle: Inspektion, Reifenservice, Bremsen und Klimaservice mit Festpreis. Termin online anfragen.') + f'''
<main id="start">
  <section class="hero">
    <div class="wrap hero-grid">
      <div class="hero-copy">
        <span class="eyebrow">Autowerkstatt in Celle</span>
        <h1>Ihr Auto in guten Händen. <em>Termin in zwei Minuten.</em></h1>
        <p class="lead">Inspektion, Reifenservice, Bremsen und Klimaservice für alle gängigen Marken. Sie wählen Leistung und Wunschtermin, wir bestätigen mit einem Festpreis, bevor wir schrauben.</p>
        <ul class="proof">
          <li>Bestätigung per E-Mail mit Vorgangsnummer</li>
          <li>Festpreis vor Reparaturbeginn</li>
          <li>Hol- und Bringservice nach Absprache</li>
        </ul>
      </div>
      <form class="quick" id="termin-form" novalidate aria-labelledby="termin-title">
        <h2 id="termin-title">Termin anfragen</h2>
        <p class="form-hint" id="termin-hint">Wählen Sie Tag und Uhrzeit. Wir bestätigen den Termin per E-Mail.</p>
        <fieldset id="fs-leistung" hidden>
          <legend>Was steht an?</legend>
          <div class="chips" id="leistung-chips"></div>
          <span class="err" data-err="leistung"></span>
        </fieldset>
        <label class="fld" id="fld-mitarbeiter" hidden>Ansprechpartner
          <select name="mitarbeiter" id="mitarbeiter"><option value="">Egal</option></select>
          <span class="err" data-err="mitarbeiter"></span>
        </label>
        <label class="fld">Wunschtag *
          <input type="date" name="datum" id="datum" required autocomplete="off">
          <span class="err" data-err="datum"></span>
        </label>
        <div class="fld" id="fs-zeit" hidden>
          <span class="lbl" id="zeit-lbl">Uhrzeit</span>
          <div class="times" id="slots" role="group" aria-labelledby="zeit-lbl"></div>
          <span class="err" data-err="uhrzeit"></span>
        </div>
        <label class="fld">Fahrzeug
          <input type="text" name="fahrzeug" autocomplete="off" placeholder="Zum Beispiel: VW Golf, Baujahr 2017">
          <span class="err" data-err="fahrzeug"></span>
        </label>
        <div class="row2">
          <label class="fld">Name *
            <input type="text" name="name" required autocomplete="name">
            <span class="err" data-err="name"></span>
          </label>
          <label class="fld">Telefon *
            <input type="tel" name="telefon" required autocomplete="tel">
            <span class="err" data-err="telefon"></span>
          </label>
        </div>
        <label class="fld">E-Mail * <small>(dorthin geht die Bestätigung)</small>
          <input type="email" name="email" required autocomplete="email">
          <span class="err" data-err="email"></span>
        </label>
        <label class="fld">Anliegen
          <textarea name="nachricht" rows="3" placeholder="Zum Beispiel: Bremsen quietschen beim Anfahren"></textarea>
          <span class="err" data-err="nachricht"></span>
        </label>
        <div class="hp" aria-hidden="true"><label>Website (bitte leer lassen)<input type="text" name="website" tabindex="-1" autocomplete="off"></label></div>
        <label class="check"><input type="checkbox" name="einwilligung" value="ja" required><span>Ich stimme der Verarbeitung meiner Angaben gemäß <a href="datenschutz.html">Datenschutzerklärung</a> zu. *</span></label>
        <span class="err" data-err="einwilligung"></span>
        <p class="form-msg" id="termin-msg" role="alert" aria-live="polite"></p>
        <button type="submit" class="btn btn-primary btn-block" id="termin-btn">Terminwunsch senden</button>
        {FALLBACK}
      </form>
    </div>
  </section>

  <section class="photo-band" aria-label="Blick in die Werkstatt">
    <div class="wrap"><div class="ph ph-wide">{img(1, 'Helle Werkstatthalle mit Hebebühne und aufgeräumtem Boden', '(max-width:1200px) 100vw, 1200px')}</div></div>
  </section>

  <section id="leistungen" class="sec">
    <div class="wrap">
      <span class="eyebrow eyebrow-d">Leistungen</span>
      <h2>Sechs Dinge, die wir jeden Tag machen.</h2>
      <div class="grid3">
        <article class="card"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#w-wrench"/></svg></span><h3>Inspektion und Wartung</h3><p>Nach Herstellervorgabe, mit Durchsicht und Kostenvoranschlag, bevor etwas getauscht wird.</p><a href="#start">Termin anfragen</a></article>
        <article class="card"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#w-tire"/></svg></span><h3>Reifenservice</h3><p>Wechsel, Einlagerung und Auswuchten. Zum Saisonwechsel am besten rechtzeitig anfragen.</p><a href="#start">Termin anfragen</a></article>
        <article class="card"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#w-brake"/></svg></span><h3>Bremsen und Fahrwerk</h3><p>Prüfung von Belägen, Scheiben und Stoßdämpfern. Sie sehen vorher, was nötig ist und was nicht.</p><a href="#start">Termin anfragen</a></article>
        <article class="card"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#w-snow"/></svg></span><h3>Klimaservice</h3><p>Prüfung und Wartung der Klimaanlage, damit sie im Sommer kühlt und der Innenraum frisch bleibt.</p><a href="#start">Termin anfragen</a></article>
        <article class="card"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#w-clip"/></svg></span><h3>HU-Vorbereitung</h3><p>Wir prüfen vorab, was zur Hauptuntersuchung auffallen könnte, und beheben es nach Ihrer Freigabe.</p><a href="#start">Termin anfragen</a></article>
        <article class="card"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true"><use href="#w-spark"/></svg></span><h3>Fahrzeugpflege</h3><p>Innen- und Außenreinigung vor dem Verkauf oder der Rückgabe, auf Wunsch im selben Termin.</p><a href="#start">Termin anfragen</a></article>
      </div>
    </div>
  </section>

  <section class="season" aria-labelledby="season-title">
    <div class="wrap season-in">
      <div>
        <span class="eyebrow">Saisonwechsel</span>
        <h2 id="season-title">Reifen rechtzeitig anfragen, Wartezeit sparen.</h2>
        <p>Zum Wechsel der Jahreszeit sind die Termine knapp. Wählen Sie Ihren Wunschtermin direkt online.</p>
      </div>
      <a class="btn btn-dark" href="#start">Reifentermin anfragen</a>
    </div>
  </section>

  <section id="ablauf" class="sec sec-steel">
    <div class="wrap">
      <span class="eyebrow">So läuft es ab</span>
      <h2>Vier Schritte, keine Überraschung.</h2>
      <ol class="steps">
        <li><span class="n">01</span><b>Anfrage</b><span>Online oder per Anruf. Sie erhalten eine Bestätigung mit Vorgangsnummer per E-Mail.</span></li>
        <li><span class="n">02</span><b>Annahme und Prüfung</b><span>Wir sehen uns das Fahrzeug an und besprechen mit Ihnen, was nötig ist.</span></li>
        <li><span class="n">03</span><b>Freigabe mit Festpreis</b><span>Sie erhalten den Preis vorab und entscheiden. Ohne Ihre Freigabe wird nichts getauscht.</span></li>
        <li><span class="n">04</span><b>Abholung</b><span>Sie erhalten das Fahrzeug mit Rechnung und Erklärung zurück, auf Wunsch mit den Altteilen.</span></li>
      </ol>
    </div>
  </section>

  <section id="zeiten" class="sec">
    <div class="wrap split">
      <div>
        <span class="eyebrow eyebrow-d">Zeiten und Anfahrt</span>
        <h2>Mitten in Celle, gut erreichbar.</h2>
        <p>Musterstraße 3, 29221 Celle. Kundenparkplätze am Haus, Bushaltestelle in drei Gehminuten.</p>
        <table class="hours">
          <caption class="sr-only">Öffnungszeiten</caption>
          <tbody>
            <tr><th scope="row">Mo bis Fr</th><td>7:30 bis 17:30 Uhr</td></tr>
            <tr><th scope="row">Samstag</th><td>nach Vereinbarung</td></tr>
            <tr><th scope="row">Sonntag</th><td>geschlossen</td></tr>
          </tbody>
        </table>
        <a class="btn btn-primary" href="#start">Termin anfragen</a>
      </div>
      <div class="roadmap" aria-hidden="true">
        <span class="road r1"></span><span class="road r2"></span><span class="road r3"></span>
        <span class="pinmark"><svg viewBox="0 0 24 24"><use href="#w-pin"/></svg></span>
        <span class="maplabel">Werkstatt Muster</span>
      </div>
    </div>
  </section>

  <section class="sec sec-soft" id="eindruecke" aria-labelledby="eindruecke-title">
    <div class="wrap">
      <span class="eyebrow eyebrow-d">Werkstatt Muster</span>
      <h2 id="eindruecke-title">Eindrücke</h2>
      <div class="gal">
        <figure><div class="ph">{img(2, 'Bremsscheibe und Bremssattel an einem Fahrzeug auf der Hebebühne', '(max-width:820px) 100vw, 640px')}</div><figcaption>Bremsen und Fahrwerk</figcaption></figure>
        <figure><div class="ph">{img(3, 'Geordnete Werkzeugwand mit Schlüsseln und Nüssen', '(max-width:820px) 100vw, 640px')}</div><figcaption>Sauber organisiert</figcaption></figure>
      </div>
      <p class="ph-note">Bildmotive mit KI-Unterstützung erstellt. Sie dienen als Symbolbilder und zeigen keinen echten Betrieb.</p>
    </div>
  </section>

  <section class="sec" id="bewertungen" aria-labelledby="bew-title">
    <div class="wrap">
      <span class="eyebrow eyebrow-d">Bewertungen</span>
      <h2 id="bew-title">Das sagen unsere Kunden.</h2>
      <div class="mk-slot" data-mk="bewertungen"></div>
      <p class="slot-alt">Fragen vor dem Termin? Rufen Sie uns an unter <a href="{TELHREF}">05141 00 00 03</a>.</p>
    </div>
  </section>

  <section id="faq" class="sec sec-soft">
    <div class="wrap narrow">
      <span class="eyebrow eyebrow-d">Häufige Fragen</span>
      <h2>Kurz beantwortet.</h2>
      <details open><summary>Wird etwas ohne meine Zustimmung repariert?</summary><p>Nein. Sie erhalten vorab einen Festpreis und entscheiden. Erst nach Ihrer Freigabe beginnen wir.</p></details>
      <details><summary>Muss ich einen Termin vereinbaren?</summary><p>Für Inspektion und Reifenservice ja, damit wir Zeit für Ihr Fahrzeug haben. Für kleine Fragen genügt ein Anruf.</p></details>
      <details><summary>Gibt es einen Hol- und Bringservice?</summary><p>Nach Absprache im näheren Umkreis. Schreiben Sie es bei der Terminanfrage in das Feld „Anliegen“.</p></details>
      <details><summary>Kann ich die alten Teile sehen?</summary><p>Auf Wunsch zeigen wir Ihnen ausgetauschte Teile und erklären, warum sie getauscht wurden.</p></details>
    </div>
  </section>

  <section id="kontakt" class="sec sec-steel">
    <div class="wrap split split-top">
      <div>
        <span class="eyebrow">Kontakt</span>
        <h2>Eine Frage? Schreiben Sie uns.</h2>
        <p>Wir antworten am selben Werktag. Oder Sie erreichen uns direkt:</p>
        <ul class="contact-list">
          <li><a href="{TELHREF}">05141 00 00 03</a> (Mo bis Fr 7:30 bis 17:30 Uhr)</li>
          <li><a href="https://wa.me/495141000003" rel="noopener">WhatsApp schreiben</a></li>
          <li><a href="mailto:{MAIL}">{MAIL}</a></li>
        </ul>
      </div>
      <div class="mk-slot mk-slot--light" data-mk="kontakt"></div>
    </div>
  </section>
</main>
''' + FOOT

IMPRESSUM = head('Impressum | Werkstatt Muster',
  'Impressum der fiktiven Beispielwerkstatt Werkstatt Muster in Celle mit Anbieterkennzeichnung und Kontaktdaten.') + f'''
<main class="legal">
  <div class="wrap narrow">
    <h1>Impressum</h1>
    <p class="note">Musterangaben für die Vorlage. Bei einer echten Seite werden alle Angaben durch die Daten des Betriebs ersetzt.</p>
    <h2>Angaben gemäß § 5 DDG</h2>
    <p>Werkstatt Muster (fiktiver Beispielbetrieb)<br>Inhaber: Max Mustermann<br>Musterstraße 3<br>29221 Celle</p>
    <h2>Kontakt</h2>
    <p>Telefon: <a href="{TELHREF}">05141 00 00 03</a><br>E-Mail: <a href="mailto:{MAIL}">{MAIL}</a></p>
    <h2>Umsatzsteuer-Identifikationsnummer</h2>
    <p>DE000000000 (Musterangabe)</p>
    <h2>Verantwortlich für den Inhalt</h2>
    <p>Max Mustermann, Anschrift wie oben.</p>
    <h2>Streitbeilegung</h2>
    <p>Wir sind nicht bereit und nicht verpflichtet, an einem Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen. (Musterangabe, bitte im Einzelfall prüfen.)</p>
    <p><a href="index.html">Zurück zur Startseite</a></p>
  </div>
</main>
''' + FOOT

DATENSCHUTZ = head('Datenschutzerklärung | Werkstatt Muster',
  'Datenschutzerklärung der Beispielwerkstatt: Server-Logs, Terminanfrage, Kontaktformular, Bewertungen und Statistik, Hosting bei Markentrix.') + f'''
<main class="legal">
  <div class="wrap narrow">
    <h1>Datenschutzerklärung</h1>
    <p class="note">Mustertext für die Vorlage. Vor der Veröffentlichung einer echten Seite werden die Angaben zum Betrieb eingesetzt und der Text rechtlich geprüft.</p>
    <h2>1. Verantwortlicher</h2>
    <p>Werkstatt Muster (fiktiver Beispielbetrieb), Max Mustermann, Musterstraße 3, 29221 Celle. Telefon <a href="{TELHREF}">05141 00 00 03</a>, E-Mail <a href="mailto:{MAIL}">{MAIL}</a>.</p>
    <h2>2. Hosting bei Markentrix und Server-Logs</h2>
    <p>Diese Website wird bei Markentrix gehostet. Beim Aufruf verarbeitet der Server technisch notwendige Daten (IP-Adresse, Datum und Uhrzeit, aufgerufene Seite, Browsertyp) in Protokolldateien, um die Seite auszuliefern und den Betrieb zu sichern. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO. Die Schriften dieser Seite liegen auf dem eigenen Server, es werden keine Daten an Schriftendienste übertragen.</p>
    <h2>3. Terminanfrage und Kontaktformular</h2>
    <p>Wenn Sie einen Termin anfragen oder das Kontaktformular nutzen, verarbeiten wir Ihre Angaben (Name, Telefon, E-Mail, Wunschtermin, Fahrzeug, Nachricht), um Ihre Anfrage zu bearbeiten und Ihnen zu antworten. Sie erhalten eine Eingangsbestätigung mit Vorgangsnummer per E-Mail. Rechtsgrundlage sind Art. 6 Abs. 1 lit. b und lit. a DSGVO (Einwilligung, jederzeit widerruflich). Die Anfragen werden über das Portal von Markentrix verarbeitet, das wir als Auftragsverarbeiter einsetzen.</p>
    <h2>4. Google-Bewertungen</h2>
    <p>Falls Bewertungen angezeigt werden, werden diese erst nach Ihrer Einwilligung über das Portal von Google geladen. Dabei kann Ihre IP-Adresse an Google übertragen werden.</p>
    <h2 id="statistik">5. Statistik und Einstellungen</h2>
    <p>Statistik und die Einwilligung dazu werden über das Portal bereitgestellt. Ohne Ihre Zustimmung wird keine Statistik erhoben. Ihre Auswahl können Sie im Footer unter „Statistik-Einstellungen“ ändern.</p>
    <h2>6. Ihre Rechte</h2>
    <p>Sie haben das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung, Datenübertragbarkeit und Widerspruch. Eine erteilte Einwilligung können Sie jederzeit widerrufen. Außerdem können Sie sich bei einer Datenschutz-Aufsichtsbehörde beschweren, in Niedersachsen bei der Landesbeauftragten für den Datenschutz.</p>
    <p><a href="index.html">Zurück zur Startseite</a></p>
  </div>
</main>
''' + FOOT

NOTFOUND = head('Seite nicht gefunden | Werkstatt Muster',
  'Die angeforderte Seite wurde nicht gefunden. Zur Startseite der Werkstatt Muster oder direkt anrufen.') + f'''
<main class="legal">
  <div class="wrap narrow">
    <h1>Diese Seite gibt es nicht.</h1>
    <p>Die Adresse stimmt nicht oder die Seite wurde verschoben. Gehen Sie zurück zur <a href="index.html">Startseite</a> oder rufen Sie uns an: <a href="{TELHREF}">05141 00 00 03</a>.</p>
    <p><a class="btn btn-primary" href="index.html">Zur Startseite</a></p>
  </div>
</main>
''' + FOOT

DANKE = head('Vielen Dank für Ihre Anfrage | Werkstatt Muster',
  'Vielen Dank, Ihre Anfrage ist bei der Werkstatt Muster eingegangen. Sie erhalten eine Bestätigung per E-Mail.') + f'''
<main class="legal" id="danke">
  <div class="wrap narrow">
    <h1>Vielen Dank. Ihre Anfrage ist eingegangen.</h1>
    <p id="danke-text">Wir melden uns am selben Werktag. Eine Bestätigung geht an Ihre E-Mail-Adresse.</p>
    <p class="ref" id="danke-ref" hidden>Ihre Vorgangsnummer: <b id="danke-nr"></b></p>
    <p>Dringend? Rufen Sie uns an: <a href="{TELHREF}">05141 00 00 03</a>.</p>
    <p><a class="btn btn-primary" href="index.html">Zur Startseite</a></p>
  </div>
</main>
''' + FOOT

SITEMAP = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>index.html</loc></url>
  <url><loc>impressum.html</loc></url>
  <url><loc>datenschutz.html</loc></url>
</urlset>
'''
ROBOTS = 'User-agent: *\nDisallow: /\n'  # Vorlage: nicht indexieren; bei einer echten Seite durch Allow und Sitemap-Zeile ersetzen
FAVSVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><path d="M6 6h52v38l-9 14H6z" fill="#ff6a1a"/><text x="32" y="40" text-anchor="middle" font-family="Arial,sans-serif" font-weight="800" font-size="24" fill="#10151a">WM</text></svg>\n'

CSS = open(os.path.join(ROOT, 'static', 'beispiel', 'werkstatt-muster', 'demo.css'), encoding='utf-8').read()
CSS = CSS.split('/* Fotos */')[0].replace('/* Beispiel-Landingpage Werkstatt Muster (fiktiv). Eigenständige Gestaltung, kein Bestandteil des Markentrix-Designsystems. */', '/* Kundenvorlage Werkstatt (fiktiv), portalfähig. */')
CSS = re.sub(r'\.ribbon\{[^}]*\}\n', '', CSS)
CSS += '''
/* Fotos */
.ph{margin:0;overflow:hidden;border-radius:14px;background:#e6e6e6;position:relative}
.ph img{display:block;position:absolute;left:0;top:0;width:100%;height:100%;object-fit:cover}
.gal{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:22px}
.gal figure{margin:0}.gal .ph{aspect-ratio:4/3}.gal figcaption{font-size:.88rem;padding:10px 2px 0}
.ph-note{font-size:.82rem;margin:14px 0 0}
.photo-band{padding:clamp(24px,4vw,48px) 0 0}.ph-wide{aspect-ratio:16/7}.ph-wide img{object-position:50% 60%}
@media (max-width:560px){.gal{grid-template-columns:minmax(0,1fr)}}
.hero-grid>*,.split>*{min-width:0}
/* Formular */
.form-hint{margin:0;font-size:.92rem;color:var(--muted)}
.fld small{font-weight:400;color:var(--muted)}
.quick .fld input,.quick .fld select,.quick .fld textarea,.form input,.form textarea{font:inherit;font-weight:400;padding:11px 12px;border:1px solid #b9c2cb;border-radius:8px;width:100%;color:var(--ink);background:#fff}
.row2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
.lbl{font-weight:600;font-size:.9rem;color:var(--ink)}
.times{display:flex;flex-wrap:wrap;gap:8px}
.times button{font:inherit;font-weight:600;font-size:.88rem;padding:8px 12px;border:1px solid #b9c2cb;border-radius:8px;background:#fff;color:var(--ink);cursor:pointer;min-height:40px}
.times button[aria-pressed="true"]{background:var(--ink);border-color:var(--ink);color:#fff}
.times button:disabled{color:#6f7a85;background:#eef1f4;text-decoration:line-through;cursor:not-allowed}
.times .times-empty{font-size:.9rem;color:var(--muted)}
.check{display:flex;gap:10px;align-items:flex-start;font-size:.88rem;font-weight:400;color:var(--ink-2)}
.check input{width:20px;height:20px;margin-top:2px;flex:none}
.err{display:block;font-size:.84rem;font-weight:600;color:#b42318;min-height:0}
.err:empty{display:none}
.form-msg{min-height:0;font-weight:600}.form-msg:empty{display:none}.form-msg.is-err{color:#b42318}
.hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
.fallback{border:1px solid #f3c9b3;background:#fff4ec;border-radius:10px;padding:12px 14px;font-size:.92rem;display:grid;gap:4px;color:var(--ink)}
.fallback[hidden]{display:none}
.btn[disabled]{opacity:.65;cursor:wait}
/* Portal-Bausteine: Platz lassen, Alternative daneben */
.mk-slot{min-height:140px;border-radius:14px}
.mk-slot[data-mk="bewertungen"]{min-height:180px}
.mk-slot--light{background:#fff;border-radius:16px;padding:6px;color:var(--ink-2)}
.slot-alt{font-size:.92rem;color:var(--muted);margin-top:14px}
.split-top{align-items:start}
.contact-list{list-style:none;padding:0;margin:14px 0 0;display:grid;gap:8px}
.contact-list a{color:#fff}
/* Rechtsseiten, Danke, 404 */
.legal{padding:clamp(36px,6vw,72px) 0 clamp(48px,7vw,96px)}
.legal h1{font-size:clamp(1.9rem,1.3rem + 2.4vw,2.8rem);margin-bottom:.6em}
.legal h2{font-size:1.25rem;margin:1.6em 0 .4em}
.note{background:var(--soft);border-left:4px solid var(--or);padding:10px 14px;border-radius:6px;font-size:.92rem}
.ref{font-size:1.1rem}
.foot a{color:var(--ink-2)}.foot-note{font-size:.82rem}
@media (max-width:480px){.row2{grid-template-columns:minmax(0,1fr)}}
.foot [data-mk]{display:inline}
.legal,.foot,.contact-list{overflow-wrap:anywhere}
'''

JS = r'''(function () {
  'use strict';
  var API = '/api/';
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function getJSON(p) {
    return fetch(API + p, { headers: { Accept: 'application/json' } }).then(function (r) {
      if (!r.ok) { var e = new Error('HTTP ' + r.status); e.status = r.status; throw e; }
      return r.json();
    });
  }
  function iso(d) { var m = d.getMonth() + 1, t = d.getDate(); return d.getFullYear() + '-' + (m < 10 ? '0' : '') + m + '-' + (t < 10 ? '0' : '') + t; }
  function qs(o) { var a = []; Object.keys(o).forEach(function (k) { if (o[k]) a.push(k + '=' + encodeURIComponent(o[k])); }); return a.length ? '?' + a.join('&') : ''; }

  /* Danke-Seite: Vorgangsnummer aus der Adresse anzeigen */
  if ($('#danke')) {
    var p = new URLSearchParams(location.search), ref = p.get('ref'), typ = p.get('typ');
    if (ref) { $('#danke-nr').textContent = ref.slice(0, 40); $('#danke-ref').hidden = false; }
    if (typ === 'termin') $('#danke-text').textContent = 'Ihr Terminwunsch ist bei uns eingegangen. Wir bestätigen ihn per E-Mail, bei Rückfragen melden wir uns telefonisch.';
  }

  var form = $('#termin-form'); if (!form) return;
  var st = { avail: null, leistungen: [], mitarbeiter: [], busy: false };
  var el = {
    fsL: $('#fs-leistung'), chips: $('#leistung-chips'), fldM: $('#fld-mitarbeiter'), selM: $('#mitarbeiter'),
    datum: $('#datum'), fsZ: $('#fs-zeit'), slots: $('#slots'), msg: $('#termin-msg'), btn: $('#termin-btn'),
    hint: $('#termin-hint'), fb: $('#api-fallback'), title: $('#termin-title')
  };
  var today = new Date(); today.setHours(0, 0, 0, 0);
  el.datum.min = iso(today);

  function setErr(name, text) { var s = $('[data-err="' + name + '"]', form); if (s) s.textContent = text || ''; }
  function clearErrs() { $$('[data-err]', form).forEach(function (s) { s.textContent = ''; }); el.msg.textContent = ''; el.msg.classList.remove('is-err'); }
  function showMsg(t, isErr) { el.msg.textContent = t; el.msg.classList.toggle('is-err', !!isErr); }
  function showFallback() { el.fb.hidden = false; }
  function sel() { var c = $('input[name="leistung"]:checked', form); return { leistung: c ? c.value : '', mitarbeiter: el.selM.value }; }

  function buildLeistungen() {
    if (!st.leistungen.length) return;
    el.chips.innerHTML = '';
    st.leistungen.forEach(function (l, i) {
      var lab = document.createElement('label'); lab.className = 'chip';
      var inp = document.createElement('input'); inp.type = 'radio'; inp.name = 'leistung'; inp.value = l.key; if (i === 0) inp.checked = true;
      var sp = document.createElement('span'); sp.textContent = l.name;
      if (l.beschreibung) lab.title = l.beschreibung;
      lab.appendChild(inp); lab.appendChild(sp); el.chips.appendChild(lab);
    });
    el.fsL.hidden = false;
  }
  function buildMitarbeiter() {
    if (st.mitarbeiter.length < 2) return;
    var s = sel().leistung;
    el.selM.innerHTML = '<option value="">Egal</option>';
    st.mitarbeiter.forEach(function (m) {
      if (s && m.leistungen && m.leistungen.length && m.leistungen.indexOf(s) < 0) return;
      var o = document.createElement('option'); o.value = m.key; o.textContent = m.name; el.selM.appendChild(o);
    });
    el.fldM.hidden = false;
  }
  function labelFor() {
    var self = st.avail && st.avail.selfBooking;
    el.btn.textContent = self ? 'Termin buchen' : 'Terminwunsch senden';
    el.title.textContent = self ? 'Termin buchen' : 'Termin anfragen';
  }
  function loadAvail() {
    var s = sel();
    return getJSON('verfuegbarkeit' + qs(s)).then(function (a) {
      st.avail = a; labelFor();
      if (a.nextFree && !el.datum.value) { el.datum.value = a.nextFree; loadSlots(); }
      else if (el.datum.value) checkDay();
    });
  }
  function dayClosed(d) {
    var a = st.avail; if (!a) return '';
    var dt = new Date(d + 'T00:00:00');
    if (isNaN(dt)) return '';
    if (dt < today) return 'Bitte wählen Sie einen Tag ab heute.';
    if ((a.closedWeekdays || []).indexOf(dt.getDay()) >= 0) return 'An diesem Wochentag ist geschlossen.';
    if ((a.blocked || []).indexOf(d) >= 0) return 'An diesem Tag sind keine Termine möglich.' + (a.nextFree ? ' Nächster freier Tag: ' + a.nextFree.split('-').reverse().join('.') + '.' : '');
    return '';
  }
  function checkDay() {
    setErr('datum', '');
    var d = el.datum.value; if (!d) { el.fsZ.hidden = true; return false; }
    var why = dayClosed(d);
    if (why) { setErr('datum', why); el.fsZ.hidden = true; el.slots.innerHTML = ''; return false; }
    return true;
  }
  function loadSlots() {
    if (!checkDay()) return;
    var s = sel(), d = el.datum.value;
    getJSON('slots' + qs({ tag: d, leistung: s.leistung, mitarbeiter: s.mitarbeiter })).then(function (r) {
      el.slots.innerHTML = ''; var any = false;
      (r.slots || []).forEach(function (x) {
        var b = document.createElement('button'); b.type = 'button'; b.textContent = x.zeit; b.setAttribute('aria-pressed', 'false');
        if (!x.frei) { b.disabled = true; b.title = 'Belegt'; } else any = true;
        b.addEventListener('click', function () {
          $$('button', el.slots).forEach(function (o) { o.setAttribute('aria-pressed', o === b ? 'true' : 'false'); });
          el.slots.setAttribute('data-wert', x.zeit); setErr('uhrzeit', '');
        });
        el.slots.appendChild(b);
      });
      el.slots.removeAttribute('data-wert');
      if (!any) { var n = document.createElement('span'); n.className = 'times-empty'; n.textContent = 'Für diesen Tag sind keine Zeiten frei. Bitte wählen Sie einen anderen Tag.'; el.slots.appendChild(n); }
      el.fsZ.hidden = false;
    }).catch(function () { showFallback(); });
  }

  /* Start: Verfügbarkeit ist Pflicht, Leistungen und Mitarbeiter sind optional */
  Promise.all([
    getJSON('verfuegbarkeit'),
    getJSON('leistungen').catch(function () { return { leistungen: [] }; }),
    getJSON('mitarbeiter').catch(function () { return { mitarbeiter: [] }; })
  ]).then(function (r) {
    st.avail = r[0]; st.leistungen = r[1].leistungen || []; st.mitarbeiter = r[2].mitarbeiter || [];
    buildLeistungen(); buildMitarbeiter(); labelFor();
    if (st.avail.nextFree) { el.datum.value = st.avail.nextFree; loadSlots(); }
  }).catch(function () { showFallback(); });

  el.datum.addEventListener('change', loadSlots);
  el.chips.addEventListener('change', function () { buildMitarbeiter(); loadAvail().then(loadSlots).catch(showFallback); });
  el.selM.addEventListener('change', function () { loadAvail().then(loadSlots).catch(showFallback); });

  function val() {
    var ok = true; clearErrs();
    function need(n, t) { var f = form.elements[n]; if (!f || !String(f.value).trim()) { setErr(n, t); ok = false; } }
    need('name', 'Bitte geben Sie Ihren Namen an.');
    need('telefon', 'Bitte geben Sie eine Telefonnummer an.');
    need('email', 'Bitte geben Sie Ihre E-Mail-Adresse an, dorthin senden wir die Bestätigung.');
    if (form.elements.email.value && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(form.elements.email.value)) { setErr('email', 'Bitte prüfen Sie die E-Mail-Adresse.'); ok = false; }
    need('datum', 'Bitte wählen Sie einen Wunschtag.');
    if (form.elements.datum.value && !checkDay()) ok = false;
    if (!form.elements.einwilligung.checked) { setErr('einwilligung', 'Bitte stimmen Sie der Datenschutzerklärung zu.'); ok = false; }
    if (!ok) { var f = $('.err:not(:empty)', form); if (f) { var inp = f.parentNode.querySelector('input,select,textarea,button'); if (inp) inp.focus(); } }
    return ok;
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault(); if (st.busy) return;
    if (!val()) return;
    var s = sel(), f = form.elements;
    var payload = {
      typ: 'termin', name: f.name.value.trim(), telefon: f.telefon.value.trim(), email: f.email.value.trim(),
      datum: f.datum.value, uhrzeit: el.slots.getAttribute('data-wert') || '', nachricht: f.nachricht.value.trim(),
      fahrzeug: f.fahrzeug.value.trim(), leistung: s.leistung, mitarbeiter: s.mitarbeiter,
      einwilligung: 'ja', website: f.website.value
    };
    st.busy = true; el.btn.disabled = true; var old = el.btn.textContent; el.btn.textContent = 'Wird gesendet …';
    fetch(API + 'anfrage', { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify(payload) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { status: r.status, body: j }; }); })
      .then(function (r) {
        if (r.status === 200 && r.body && r.body.ok) { location.href = 'danke.html?typ=termin&ref=' + encodeURIComponent(r.body.ref || ''); return; }
        if (r.status === 422 && r.body && r.body.errors) {
          Object.keys(r.body.errors).forEach(function (k) { setErr(k, r.body.errors[k]); });
          if (r.body.errors.uhrzeit) { showMsg('Diese Uhrzeit ist inzwischen vergeben. Bitte wählen Sie eine andere.', true); loadSlots(); }
          else showMsg('Bitte prüfen Sie die markierten Felder.', true);
        } else if (r.status === 429) { showMsg('Bitte versuchen Sie es später noch einmal.', true); }
        else { showMsg('Das Senden hat nicht geklappt. Eingaben bleiben erhalten.', true); showFallback(); }
      })
      .catch(function () { showMsg('Keine Verbindung. Ihre Eingaben bleiben erhalten.', true); showFallback(); })
      .then(function () { st.busy = false; el.btn.disabled = false; el.btn.textContent = old; });
  });
})();
'''

def main():
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    for n, t in [('index.html', INDEX), ('impressum.html', IMPRESSUM), ('datenschutz.html', DATENSCHUTZ), ('404.html', NOTFOUND), ('danke.html', DANKE),
                 ('sitemap.xml', SITEMAP), ('robots.txt', ROBOTS), ('favicon.svg', FAVSVG), ('assets/style.css', CSS), ('assets/app.js', JS)]:
        w(n, t)
    for n in (1, 2, 3):
        for s in (800, 1400):
            p = os.path.join(OUT, 'assets', 'img', f'{n}-{s}.webp'); os.makedirs(os.path.dirname(p), exist_ok=True)
            shutil.copy(os.path.join(SRC_IMG, f'{n}-{s}.webp'), p)
    fd = os.path.join(OUT, 'assets', 'fonts'); os.makedirs(fd, exist_ok=True)
    for f in os.listdir(FONTS):
        if f.endswith('.woff2') or f == 'fonts.css': shutil.copy(os.path.join(FONTS, f), fd)
    from PIL import Image
    Image.open(os.path.join(ROOT, 'static', 'apple-touch-icon.png')).convert('RGBA').save(os.path.join(OUT, 'favicon.ico'), format='ICO', sizes=[(16, 16), (32, 32), (48, 48)])
    print('website-fertig gebaut:', sum(len(f) for _, _, f in os.walk(OUT)), 'Dateien')
    # Vorschau-Kopie
    if os.path.isdir(PREV): shutil.rmtree(PREV)
    shutil.copytree(OUT, PREV)
    for dp, _, fs in os.walk(PREV):
        for f in fs:
            if f.endswith('.html'):
                p = os.path.join(dp, f); t = open(p, encoding='utf-8').read()
                t = t.replace('<script src="assets/app.js" defer></script>', '<script src="assets/vorschau-api.js"></script>\n<script src="assets/app.js" defer></script>')
                open(p, 'w', encoding='utf-8').write(t)
    shutil.copy(os.path.join(os.path.dirname(__file__), 'vorschau-api.js'), os.path.join(PREV, 'assets', 'vorschau-api.js'))
    shutil.copy(os.path.join(os.path.dirname(__file__), 'vorschau.css'), os.path.join(PREV, 'assets', 'vorschau.css'))
    print('Vorschau:', PREV)

if __name__ == '__main__':
    main()
