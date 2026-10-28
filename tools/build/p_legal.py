# -*- coding: utf-8 -*-
from common import *

ADDR = '''<address>
<strong>Burnout Celler-Kartbahn GmbH</strong><br>
Waldweg 100<br>29221 Celle<br>
Telefon: <a href="tel:+495141908650">05141 908650</a><br>
Telefax: 05141 908652<br>
E-Mail: <a href="mailto:team@celler-kartbahn.com">team@celler-kartbahn.com</a>
</address>'''

# ---------------- IMPRESSUM ----------------
html = head("Impressum | Burnout Celler-Kartbahn GmbH, Celle", "Impressum der Burnout Celler-Kartbahn GmbH, Waldweg 100, 29221 Celle. Geschäftsführer Christian Sprunk, Amtsgericht Lüneburg HRB 205167, USt-IdNr. DE 297 391 967.", breadcrumb("Impressum","impressum.html")) + header()
html += f'''
<section class="section"><div class="wrap prose">
<h1>Impressum</h1>
<h2>Angaben gemäß § 5 DDG</h2>
{ADDR}
<p><strong>Vertreten durch den Geschäftsführer:</strong> Christian Sprunk</p>
<p><strong>Registereintrag:</strong> Handelsregister beim Amtsgericht Lüneburg, HRB 205167</p>
<p><strong>Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG:</strong> DE 297 391 967</p>
<p><strong>Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV:</strong> Christian Sprunk, Waldweg 100, 29221 Celle</p>
<p>Dieses Impressum gilt auch für unsere Facebook-Seite <a href="https://www.facebook.com/BurnoutCellerKartbahn/" rel="noopener" target="_blank">facebook.com/BurnoutCellerKartbahn</a>.</p>

<h2>Streitbeilegung</h2>
<p>Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit: <a href="https://ec.europa.eu/consumers/odr/" rel="noopener" target="_blank">https://ec.europa.eu/consumers/odr/</a>. Unsere E-Mail-Adresse findet ihr oben im Impressum.</p>
<p>Wir sind nicht bereit und nicht verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen (§ 36 VSBG).</p>

<h2>Haftung für Inhalte</h2>
<p>Die Inhalte unserer Seiten wurden mit größter Sorgfalt erstellt. Für die Richtigkeit, Vollständigkeit und Aktualität der Inhalte können wir jedoch keine Gewähr übernehmen. Als Diensteanbieter sind wir gemäß § 7 Abs. 1 DDG für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 DDG sind wir als Diensteanbieter jedoch nicht verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen oder nach Umständen zu forschen, die auf eine rechtswidrige Tätigkeit hinweisen. Verpflichtungen zur Entfernung oder Sperrung der Nutzung von Informationen nach den allgemeinen Gesetzen bleiben hiervon unberührt. Eine diesbezügliche Haftung ist jedoch erst ab dem Zeitpunkt der Kenntnis einer konkreten Rechtsverletzung möglich. Bei Bekanntwerden von entsprechenden Rechtsverletzungen werden wir diese Inhalte umgehend entfernen.</p>

<h2>Haftung für Links</h2>
<p>Unser Angebot enthält Links zu externen Websites Dritter, auf deren Inhalte wir keinen Einfluss haben. Deshalb können wir für diese fremden Inhalte auch keine Gewähr übernehmen. Für die Inhalte der verlinkten Seiten ist stets der jeweilige Anbieter oder Betreiber der Seiten verantwortlich. Die verlinkten Seiten wurden zum Zeitpunkt der Verlinkung auf mögliche Rechtsverstöße überprüft. Rechtswidrige Inhalte waren zum Zeitpunkt der Verlinkung nicht erkennbar. Eine permanente inhaltliche Kontrolle der verlinkten Seiten ist jedoch ohne konkrete Anhaltspunkte einer Rechtsverletzung nicht zumutbar. Bei Bekanntwerden von Rechtsverletzungen werden wir derartige Links umgehend entfernen.</p>

<h2>Urheberrecht</h2>
<p>Die durch die Seitenbetreiber erstellten Inhalte und Werke auf diesen Seiten unterliegen dem deutschen Urheberrecht. Die Vervielfältigung, Bearbeitung, Verbreitung und jede Art der Verwertung außerhalb der Grenzen des Urheberrechts bedürfen der schriftlichen Zustimmung des jeweiligen Autors bzw. Erstellers. Downloads und Kopien dieser Seite sind nur für den privaten, nicht kommerziellen Gebrauch gestattet. Soweit die Inhalte auf dieser Seite nicht vom Betreiber erstellt wurden, werden die Urheberrechte Dritter beachtet. Insbesondere werden Inhalte Dritter als solche gekennzeichnet. Solltet ihr trotzdem auf eine Urheberrechtsverletzung aufmerksam werden, bitten wir um einen entsprechenden Hinweis. Bei Bekanntwerden von Rechtsverletzungen werden wir derartige Inhalte umgehend entfernen.</p>
<p><strong>Bildnachweise:</strong> Alle Fotos © Burnout Celler-Kartbahn GmbH. Kartendaten: © <a href="https://www.openstreetmap.org/copyright" rel="noopener" target="_blank">OpenStreetMap</a>-Mitwirkende (ODbL). Schrift „Inter“ von Rasmus Andersson, SIL Open Font License 1.1.</p>
</div></section>
''' + footer() + end()
write("impressum.html", html)

# ---------------- DATENSCHUTZ ----------------
html = head("Datenschutzerklärung | Burnout Celler-Kartbahn GmbH", "Datenschutzerklärung der Burnout Celler-Kartbahn GmbH: Hosting bei Markentrix, Server-Logs, Kontakt- und Buchungsformulare, Gutscheinbestellung, PayPal, Google-Bewertungen, OpenStreetMap-Karte, WhatsApp und Besucherstatistik ohne Cookies.", breadcrumb("Datenschutz","datenschutz.html")) + header()
html += f'''
<section class="section"><div class="wrap prose">
<h1>Datenschutzerklärung</h1>
<p class="lead">Wir freuen uns über euren Besuch auf unserer Website. Der Schutz eurer personenbezogenen Daten ist uns wichtig. Nachfolgend informieren wir euch gemäß Art. 13 DSGVO darüber, welche Daten wir verarbeiten, zu welchem Zweck und welche Rechte ihr habt.</p>
<div class="toc"><strong>Inhalt</strong><ol>
<li><a href="#verantwortlicher">Verantwortlicher</a></li><li><a href="#hosting">Hosting &amp; Server-Logs</a></li><li><a href="#formulare">Kontakt- und Buchungsformulare</a></li><li><a href="#gutschein">Gutscheinbestellung &amp; Widerruf</a></li><li><a href="#paypal">Zahlung mit PayPal</a></li><li><a href="#statistik">Besucherstatistik &amp; Einwilligung</a></li><li><a href="#karte">Karte (OpenStreetMap)</a></li><li><a href="#bewertungen">Google-Bewertungen</a></li><li><a href="#whatsapp">WhatsApp &amp; externe Links</a></li><li><a href="#rennlizenz">Registrierung vor Ort / Rennlizenz</a></li><li><a href="#rechte">Eure Rechte</a></li><li><a href="#sicherheit">Datensicherheit &amp; Änderungen</a></li></ol></div>

<h2 id="verantwortlicher">1. Verantwortlicher</h2>
{ADDR}
<p>Vertreten durch den Geschäftsführer Christian Sprunk. Ein Datenschutzbeauftragter ist nicht bestellt, da die gesetzlichen Voraussetzungen hierfür nicht vorliegen. Bei Fragen zum Datenschutz erreicht ihr uns unter den oben genannten Kontaktdaten.</p>

<h2 id="hosting">2. Hosting &amp; Server-Logs</h2>
<p>Diese Website wird bei Markentrix gehostet und über das Markentrix-Portal betrieben. Beim Aufruf unserer Seiten verarbeitet der Server automatisch Informationen, die euer Browser übermittelt (Server-Logfiles): IP-Adresse, Datum und Uhrzeit des Zugriffs, aufgerufene Seite bzw. Datei, übertragene Datenmenge, Browsertyp und -version, Betriebssystem, Referrer-URL. Diese Daten sind technisch erforderlich, um die Website auszuliefern, und dienen der Sicherheit und Stabilität des Systems (z.&nbsp;B. Abwehr von Angriffen). Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse an einem sicheren und funktionsfähigen Betrieb). Logfiles werden nach kurzer Zeit automatisch gelöscht, sofern keine Aufbewahrung zu Beweiszwecken bei einem Sicherheitsvorfall erforderlich ist.</p>
<p>Mit dem Hosting-Anbieter besteht ein Vertrag zur Auftragsverarbeitung nach Art. 28 DSGVO. Die Verarbeitung findet auf Servern in Deutschland bzw. der EU statt.</p>
<p>Schriften, Skripte und Bilder werden ausschließlich von unserem eigenen Server geladen; es werden keine Inhalte von Drittanbietern (z.&nbsp;B. Google Fonts, CDN-Dienste) automatisch nachgeladen.</p>

<h2 id="formulare">3. Kontakt- und Buchungsformulare</h2>
<p>Wenn ihr uns über das Kontaktformular, das Online-Buchungsformular oder die Gutscheinbestellung schreibt, verarbeiten wir die von euch eingegebenen Daten (z.&nbsp;B. Name, E-Mail-Adresse, Telefonnummer, Firma, Wunschtermin, Teilnehmerzahl, Alter der Kinder, Nachricht) zur Bearbeitung eurer Anfrage bzw. Buchung und für eventuelle Rückfragen. Die Übermittlung erfolgt verschlüsselt (TLS) an das Markentrix-Portal, über das wir die Anfragen empfangen und bearbeiten. Ihr erhaltet automatisch eine Eingangsbestätigung mit Vorgangsnummer an die angegebene E-Mail-Adresse.</p>
<p>Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO (Vertrag bzw. vorvertragliche Maßnahmen) sowie eure Einwilligung nach Art. 6 Abs. 1 lit. a DSGVO, die ihr über die Checkbox im Formular erteilt und jederzeit mit Wirkung für die Zukunft widerrufen könnt. Zum Schutz vor Spam enthalten die Formulare ein unsichtbares Prüffeld; es werden keine Cookies gesetzt und keine Drittanbieter-Captchas eingebunden.</p>
<p>Wir speichern die Daten, solange es zur Bearbeitung eurer Anfrage bzw. zur Durchführung der Buchung erforderlich ist. Daten, die Teil einer Buchung oder Rechnung sind, bewahren wir nach den handels- und steuerrechtlichen Vorschriften (§ 147 AO, § 257 HGB) bis zu zehn Jahre auf. Sonstige Anfragen löschen wir spätestens zwölf Monate nach Abschluss der Kommunikation.</p>

<h2 id="gutschein">4. Gutscheinbestellung &amp; Widerruf</h2>
<p>Bei der Bestellung eines Gutscheins verarbeiten wir eure Angaben (Name, E-Mail, ggf. Telefon, Betrag, Beschenkter, Widmung, Zustellart) zur Vertragsdurchführung, zum Versand des Gutscheins und zur Abwicklung der Zahlung (Art. 6 Abs. 1 lit. b DSGVO). Das Gleiche gilt für Erklärungen über unser Widerrufsformular. Die Aufbewahrung richtet sich nach den gesetzlichen Fristen (siehe Ziffer 3).</p>

<h2 id="paypal">5. Zahlung mit PayPal</h2>
<p>Für den Kauf von Gutscheinen bieten wir die Zahlung über PayPal an. Anbieter ist PayPal (Europe) S.à r.l. et Cie, S.C.A., 22-24 Boulevard Royal, L-2449 Luxemburg. Die PayPal-Schaltfläche wird über das Markentrix-Portal bereitgestellt. Beim Klick auf die Schaltfläche bzw. beim Bezahlvorgang werden die für die Zahlung notwendigen Daten (Name, Betrag, Verwendungszweck, ggf. E-Mail-Adresse) an PayPal übermittelt; die Zahlung selbst wickelt ihr in eurem PayPal-Konto ab. PayPal kann dabei eigene Cookies setzen und Daten in Drittländer übermitteln; es gelten die Datenschutzhinweise von PayPal: <a href="https://www.paypal.com/de/legalhub/privacy-full" rel="noopener" target="_blank">paypal.com/de/legalhub/privacy-full</a>. Rechtsgrundlage ist Art. 6 Abs. 1 lit. b DSGVO (Vertragsdurchführung). Das Geld geht direkt an uns; wir speichern keine Zahlungs- oder Kontodaten auf dieser Website.</p>

<h2 id="statistik">6. Besucherstatistik &amp; Einwilligung</h2>
<p>Zur Verbesserung unseres Angebots erfassen wir über das Markentrix-Portal eine anonyme Reichweitenstatistik (aufgerufene Seite, Zeitpunkt, Bildschirmbreite, Seitentitel). Dabei werden keine Cookies gesetzt, keine Nutzerprofile gebildet und IP-Adressen nicht dauerhaft gespeichert. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse an der Reichweitenmessung). Soweit das Portal eine Einwilligung für Statistik oder weitere Dienste vorsieht, könnt ihr diese über den Link „Statistik-Einstellungen“ in der Fußzeile jederzeit einsehen, erteilen oder widerrufen (Art. 6 Abs. 1 lit. a DSGVO, § 25 TDDDG).</p>

<h2 id="karte">7. Karte (OpenStreetMap) – Zwei-Klick-Lösung</h2>
<p>Auf den Seiten „Start“ und „Kontakt“ bieten wir eine Anfahrtskarte an. Die Karte wird erst geladen, wenn ihr auf „Karte laden“ klickt (Zwei-Klick-Lösung). Vorher werden keine Daten an Dritte übertragen. Mit dem Klick willigt ihr ein (Art. 6 Abs. 1 lit. a DSGVO, § 25 Abs. 1 TDDDG), dass euer Browser eine Verbindung zu den Servern der OpenStreetMap Foundation (St John's Innovation Centre, Cowley Road, Cambridge, CB4 0WS, Großbritannien) aufbaut und dabei eure IP-Adresse sowie Browserdaten übermittelt werden. Für Großbritannien liegt ein Angemessenheitsbeschluss der EU-Kommission vor. Datenschutzhinweise: <a href="https://wiki.osmfoundation.org/wiki/Privacy_Policy" rel="noopener" target="_blank">wiki.osmfoundation.org/wiki/Privacy_Policy</a>. Die Links „Route planen“ führen zu externen Kartendiensten (Google Maps, OpenStreetMap); dort gelten die jeweiligen Datenschutzhinweise.</p>

<h2 id="bewertungen">8. Google-Bewertungen</h2>
<p>Auf der Startseite zeigen wir Bewertungen unserer Gäste aus dem Google-Unternehmensprofil an. Die Bewertungen werden über das Markentrix-Portal bereitgestellt; beim Laden werden keine Daten von euch direkt an Google übermittelt. Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse an der Darstellung von Kundenmeinungen). Wenn ihr selbst eine Bewertung bei Google abgeben möchtet, gelten die Datenschutzbestimmungen von Google Ireland Limited, Gordon House, Barrow Street, Dublin 4, Irland: <a href="https://policies.google.com/privacy" rel="noopener" target="_blank">policies.google.com/privacy</a>.</p>

<h2 id="whatsapp">9. WhatsApp &amp; externe Links</h2>
<p>Wir bieten euch an, uns per WhatsApp zu kontaktieren. Beim Klick auf den WhatsApp-Link öffnet sich die WhatsApp-App bzw. WhatsApp Web; erst dann werden Daten an WhatsApp Ireland Limited (4 Grand Canal Square, Dublin 2, Irland) übermittelt. Für die Kommunikation gelten die Datenschutzhinweise von WhatsApp: <a href="https://www.whatsapp.com/legal/privacy-policy-eea" rel="noopener" target="_blank">whatsapp.com/legal/privacy-policy-eea</a>. Wir nutzen WhatsApp ausschließlich zur Beantwortung eurer Anfragen (Art. 6 Abs. 1 lit. b und f DSGVO). Bitte sendet uns über WhatsApp keine besonders sensiblen Daten.</p>
<p>Unsere Website enthält Links zu externen Seiten (z.&nbsp;B. Facebook, Dartraum Celle, Sodikart). Beim Anklicken verlasst ihr unsere Website; für die Datenverarbeitung dort sind die jeweiligen Betreiber verantwortlich.</p>

<h2 id="rennlizenz">10. Registrierung vor Ort / Rennlizenz</h2>
<p>Beim ersten Besuch registriert sich jeder Fahrer aus versicherungstechnischen Gründen an der Anmeldung und erhält eine Rennlizenz. Die dabei erhobenen Daten (Name, Geburtsdatum, Kontaktdaten, bei Minderjährigen die Einverständniserklärung der Erziehungsberechtigten) und die Rundenzeiten werden in unserem Zeitnahme- und Lizenzsystem verarbeitet, um die Teilnahme zu ermöglichen, Rennergebnisse bereitzustellen und unsere Versicherungspflichten zu erfüllen (Art. 6 Abs. 1 lit. b, c und f DSGVO). Hinweise zur Datenverarbeitung in der Rennlizenz-App erhaltet ihr bei der Registrierung vor Ort.</p>

<h2 id="rechte">11. Eure Rechte</h2>
<p>Ihr habt gegenüber uns folgende Rechte hinsichtlich der euch betreffenden personenbezogenen Daten:</p>
<ul>
<li>Recht auf Auskunft (Art. 15 DSGVO)</li>
<li>Recht auf Berichtigung (Art. 16 DSGVO) und Löschung (Art. 17 DSGVO)</li>
<li>Recht auf Einschränkung der Verarbeitung (Art. 18 DSGVO)</li>
<li>Recht auf Datenübertragbarkeit (Art. 20 DSGVO)</li>
<li>Recht auf Widerspruch gegen Verarbeitungen auf Grundlage von Art. 6 Abs. 1 lit. f DSGVO (Art. 21 DSGVO)</li>
<li>Recht, eine erteilte Einwilligung jederzeit mit Wirkung für die Zukunft zu widerrufen (Art. 7 Abs. 3 DSGVO)</li>
</ul>
<p>Zur Ausübung eurer Rechte genügt eine formlose Nachricht an <a href="mailto:team@celler-kartbahn.com">team@celler-kartbahn.com</a>. Ihr habt zudem das Recht, euch bei einer Datenschutz-Aufsichtsbehörde zu beschweren. Zuständig für uns ist die Landesbeauftragte für den Datenschutz Niedersachsen, Prinzenstraße 5, 30159 Hannover, <a href="https://www.lfd.niedersachsen.de" rel="noopener" target="_blank">www.lfd.niedersachsen.de</a>.</p>

<h2 id="sicherheit">12. Datensicherheit &amp; Änderungen</h2>
<p>Unsere Website nutzt eine SSL/TLS-Verschlüsselung; alle Formulardaten werden verschlüsselt übertragen. Eine Bereitstellung eurer Daten ist weder gesetzlich noch vertraglich vorgeschrieben; ohne die als Pflichtfelder gekennzeichneten Angaben können wir Anfragen und Buchungen jedoch nicht bearbeiten. Eine automatisierte Entscheidungsfindung oder ein Profiling findet nicht statt.</p>
<p>Wir behalten uns vor, diese Datenschutzerklärung anzupassen, wenn sich die Rechtslage oder unsere Website ändert. Stand: Oktober 2026.</p>
</div></section>
''' + footer() + end()
write("datenschutz.html", html)

# ---------------- AGB ----------------
html = head("AGB | Burnout Celler-Kartbahn GmbH", "Allgemeine Geschäftsbedingungen der Burnout Celler-Kartbahn GmbH: Buchung, Preise, Stornierung, Haftung, Nutzungsbedingungen der Karts und der Kartbahn, Gutscheine.", breadcrumb("AGB","agb.html")) + header()
html += '''
<section class="section"><div class="wrap prose">
<h1>Allgemeine Geschäftsbedingungen (AGB)</h1>
<p class="lead">der Burnout Celler-Kartbahn GmbH, Waldweg 100, 29221 Celle</p>

<h2>§ 1 Allgemeines – Geltungsbereich</h2>
<p>(1) Die nachstehenden Allgemeinen Geschäftsbedingungen gelten für alle Angebote, Annahmeerklärungen und Leistungen der Burnout Celler-Kartbahn GmbH, einschließlich Buchungen und Gutscheinbestellungen über unsere Website.</p>
<p>(2) Abweichende, entgegenstehende oder ergänzende Allgemeine Geschäftsbedingungen unserer Kunden (einheitliche Bezeichnung für Vertragspartner, Nutzer der Kartbahn usw.) werden nicht Vertragsbestandteil, es sei denn, ihrer Geltung wird durch uns ausdrücklich schriftlich zugestimmt.</p>

<h2>§ 2 Vertragsschluss / Buchung</h2>
<p>(1) Unsere Angebote sind bis zur Buchungsbestätigung durch uns freibleibend.</p>
<p>(2) Mit der Buchung erklärt der Kunde verbindlich, den Auftrag erteilen zu wollen. Wir sind berechtigt, das in der Buchung liegende Vertragsangebot innerhalb von zwei Wochen nach Eingang bei uns anzunehmen. Die Annahme kann entweder in Textform durch eine Buchungsbestätigung oder durch Bereitstellung der Leistung erklärt werden.</p>
<p>(3) Den Eingang von Buchungen auf elektronischem Wege (Online-Buchung, E-Mail) bestätigen wir in aller Regel unverzüglich mit einer Vorgangsnummer. Unsere Eingangsbestätigung stellt jedoch noch keine verbindliche Annahme des Vertragsangebots des Kunden dar, sondern erst die nachfolgende Buchungsbestätigung.</p>
<p>(4) Vertragssprache ist Deutsch. Der Vertragstext wird von uns gespeichert; der Kunde erhält die wesentlichen Vertragsdaten mit der Buchungsbestätigung per E-Mail.</p>

<h2>§ 3 Leistungen, Preise, Zahlung, Aufrechnung</h2>
<p>(1) Wir sind verpflichtet, die vom Kunden gebuchten Leistungen bereitzuhalten und die vereinbarten Leistungen zu erbringen. Die vertraglich vereinbarten Leistungen ergeben sich ausschließlich aus unserer Buchungsbestätigung.</p>
<p>(2) Überschreitet der Zeitraum zwischen Vertragsabschluss und Leistungserbringung 4 Monate, so behalten wir uns das Recht vor, Preisänderungen auch ohne vorherige Ankündigung vorzunehmen.</p>
<p>(3) Wir sind berechtigt, bei Vertragsschluss vom Kunden eine angemessene Vorauszahlung oder Sicherheitsleistung in Form einer Kreditkartengarantie, einer Anzahlung oder Ähnlichem zu verlangen.</p>
<p>(4) Preise für die Nutzung der Kartbahn und die damit in Zusammenhang stehenden Leistungen sind vorab zur Zahlung durch unsere Kunden fällig. Soweit nichts anderes vereinbart ist, erfolgt die Zahlung vor Ort in bar oder per EC-Karte. Alle Preise verstehen sich in Euro inklusive der gesetzlichen Umsatzsteuer.</p>
<p>(5) Der Kunde kann nur mit einer unstreitigen oder rechtskräftig festgestellten Forderung gegenüber einer Forderung der Burnout Celler-Kartbahn GmbH aufrechnen oder mindern bzw. ein Zurückbehaltungsrecht ausüben.</p>

<h2>§ 4 Stornierung durch den Kunden / Nichtinanspruchnahme der Leistungen</h2>
<p>(1) Für alle zustande gekommenen Buchungen über die Nutzung unserer Kartbahn und damit verbundener Leistungen gewähren wir unseren Kunden grundsätzlich eine Umbuchungs- und Stornierungsmöglichkeit. Der Zeitpunkt der Stornierung bestimmt dabei den Anspruch der Burnout Celler-Kartbahn GmbH auf eine angemessene Vergütung; ersparte Aufwendungen sind damit abgegolten. Es gelten folgende Stornierungsgebühren:</p>
<div class="table-wrap"><table><tbody>
<tr><td>bis 28 Tage vor Leistungsbeginn</td><td class="price">25 % des Leistungspreises</td></tr>
<tr><td>bis 14 Tage vor Leistungsbeginn</td><td class="price">50 % des Leistungspreises</td></tr>
<tr><td>bis 7 Tage vor Leistungsbeginn</td><td class="price">75 % des Leistungspreises</td></tr>
<tr><td>ab 6 Tage vor Leistungsbeginn oder bei Nichtinanspruchnahme</td><td class="price">100 % des Leistungspreises</td></tr>
</tbody></table></div>
<p>(2) Dem Kunden bleibt der Nachweis eines niedrigeren, uns der Nachweis eines höheren Schadens vorbehalten.</p>
<p>(3) Umbuchungen und/oder Stornierungen haben in Textform zu erfolgen und sind an folgende Adresse zu richten: Burnout Celler-Kartbahn GmbH, Waldweg 100, 29221 Celle, oder <a href="mailto:team@celler-kartbahn.com">team@celler-kartbahn.com</a>.</p>
<p>(4) Das gesetzliche Widerrufsrecht für Verbraucher bei Fernabsatzverträgen bleibt unberührt; für Freizeitdienstleistungen mit einem festen Termin besteht gemäß § 312g Abs. 2 Nr. 9 BGB kein Widerrufsrecht. Näheres in unserer <a href="widerruf.html">Widerrufsbelehrung</a>.</p>

<h2>§ 5 Rücktritt durch die Burnout Celler-Kartbahn GmbH</h2>
<p>(1) Kommt der Kunde seiner Zahlungsverpflichtung nicht nach, so sind wir zum Rücktritt vom Vertrag berechtigt. Das gilt auch für den Fall, dass eine vereinbarte oder gemäß § 3 Abs. 3 von uns verlangte Vorauszahlung auch nach Verstreichen einer von uns gesetzten angemessenen Nachfrist nicht geleistet wird.</p>
<p>(2) Ferner behalten wir uns das Recht vor, vom Vertrag zurückzutreten, falls</p>
<ol type="a">
<li>höhere Gewalt oder sonstige von uns nicht zu vertretende Hinderungsgründe (z.&nbsp;B. Brand, Streik) die Erfüllung des Vertrages unzumutbar machen, soweit die Umstände zum Leistungszeitpunkt noch andauern. In diesem Fall wird der Kunde unverzüglich über das Leistungshindernis informiert und seine bereits erbrachten Gegenleistungen werden unverzüglich erstattet;</li>
<li>wir begründeten Anlass zu der Annahme haben, dass die Inanspruchnahme der gebuchten Leistungen durch den Kunden den reibungslosen Geschäftsbetrieb, die Sicherheit oder das Ansehen der Burnout Celler-Kartbahn GmbH in der Öffentlichkeit gefährden kann, ohne dass dies unserem Herrschafts- bzw. Organisationsbereich zuzurechnen ist.</li>
</ol>
<p>(3) Dem Kunden stehen aufgrund des Rücktritts keinerlei Schadensersatzansprüche zu. Erfolgt der Rücktritt der Burnout Celler-Kartbahn GmbH aus den unter b) genannten Gründen oder wegen Nichtleistung der Zahlungsverpflichtung durch den Kunden, so steht uns ein Anspruch auf Schadensersatz wegen Pflichtverletzung zu.</p>

<h2>§ 6 Haftungsbeschränkungen</h2>
<p>(1) Wir haften für alle Schäden, die durch schuldhafte Verletzung einer vertragswesentlichen Pflicht durch uns, unsere gesetzlichen Vertreter, Mitarbeiter oder unsere Erfüllungsgehilfen verursacht wurden oder die auf grobe Fahrlässigkeit oder Vorsatz zurückzuführen sind.</p>
<p>(2) Im Falle der Verletzung einer vertragswesentlichen Pflicht ist bei einfacher Fahrlässigkeit unsere Haftung auf den vertragstypischen, vorhersehbaren Schaden begrenzt.</p>
<p>(3) Die Haftung wegen Verletzung des Lebens, des Körpers oder der Gesundheit sowie die Haftung nach dem Produkthaftungsgesetz, die Haftung bei arglistig verschwiegenen Fehlern wie auch die Haftung bei Übernahme einer Garantie für die Beschaffenheit einer Sache bleibt davon unberührt.</p>

<h2>§ 7 Zusatzbedingungen für die Nutzung der Karts / Kartbahn</h2>
<p>(1) Das Betreten des Geländes und der Aufenthalt auf der Anlage sowie die Benutzung der Karts und das Befahren der Kartbahn sowie die Teilnahme an allen dortigen Aktivitäten geschieht auf eigene Gefahr und eigenes Risiko des Kunden.</p>
<p>(2) Bei der Benutzung der Karts und dem Befahren der Kartbahn ist den Anweisungen und Benutzungshinweisen unserer Mitarbeiter ausnahmslos Folge zu leisten. Für Schäden, die durch Zuwiderhandlung oder unsachgemäße Benutzung verursacht werden, übernehmen wir keine Haftung, es sei denn, dass der Schaden durch fehlerhafte Benutzungshinweise oder durch einen uns vorwerfbar nicht ordnungsgemäßen Zustand der Karts oder Einrichtungen verursacht worden ist.</p>
<p>(3) Die Benutzung der Karts ist nur Kunden gestattet, die an keinerlei körperlichen Gebrechen leiden, die nicht unter Alkohol-, Drogen- oder Medikamenteneinfluss stehen und nicht zu einer gesundheitlichen Risikogruppe gehören (z.&nbsp;B. Bluthochdruck, Herzerkrankungen, Schwangerschaft). Auf die besondere Gefährdung der zu diesen Risikogruppen gehörenden Kunden wird hingewiesen. Kunden, die trotz des Verbotes in alkoholisiertem Zustand ein Kart benutzen, werden ausgeschlossen; das Ticket verfällt entschädigungslos. Die Kunden erklären sich mit einer Alkoholkontrolle einverstanden.</p>
<p>(4) Mindestalter und Mindestgröße: Kinderkart ab 8 Jahren und 1,25 m; Rennkart ab 13 Jahren und 1,55 m (mit Karterfahrung ab 12 Jahren und 1,55 m); Beifahrer im Doppelsitzer ab 4 Jahren und 1,10 m, am Steuer eine volljährige Person. Minderjährige benötigen die schriftliche Einverständniserklärung eines Erziehungsberechtigten. Die Entscheidung über die Zulassung zu einem Kart trifft ausschließlich das Bahnpersonal.</p>
<p>(5) Für Schäden, die durch eigenes Verschulden des Kunden, unfallbedingt oder durch unsachgemäße Benutzung oder dadurch entstehen, dass den Anweisungen unserer Mitarbeiter nicht Folge geleistet wird, übernimmt der Kunde die uneingeschränkte Haftung. Sofern in diesen Fällen Dritte zu Schaden kommen, stellt der Kunde die Burnout Celler-Kartbahn GmbH von etwaigen Haftungsansprüchen dieser Dritten frei.</p>
<p>(6) Wir übernehmen keine Haftung für Schäden, die durch Fahrer oder Nutzer anderer Karts, sonstige Nutzer der Kartbahn oder Dritte verursacht werden.</p>
<p>(7) Vorstehende Haftungsbeschränkungen gelten nicht für Schäden, die auf grobe Fahrlässigkeit oder Vorsatz der Burnout Celler-Kartbahn GmbH, deren Mitarbeiter oder Erfüllungsgehilfen beruhen, oder für Schäden aus der schuldhaften Verletzung einer wesentlichen Vertragspflicht.</p>
<p>(8) Tickets für Ticketfahrten sind nicht übertragbar und müssen am Kaufdatum verfahren werden. Das Mitbringen eigener Speisen und Getränke ist nicht gestattet.</p>

<h2>§ 8 Gutscheine</h2>
<p>(1) Gutscheine können über unsere Website bestellt oder vor Ort erworben werden. Der Gutschein wird nach Zahlungseingang per E-Mail (PDF) zugesandt oder vor Ort ausgehändigt; den Gutscheincode vergibt die Burnout Celler-Kartbahn GmbH.</p>
<p>(2) Gutscheine sind für alle Leistungen der Burnout Celler-Kartbahn GmbH einlösbar und werden mit dem zum Einlösezeitpunkt gültigen Preis verrechnet. Eine Barauszahlung des Gutscheinwerts oder eines Restguthabens ist ausgeschlossen; ein Restguthaben bleibt bis zum Ablauf der Gültigkeit erhalten.</p>
<p>(3) Gutscheine sind, sofern auf dem Gutschein nichts anderes angegeben ist, drei Jahre ab Ende des Ausstellungsjahres gültig (§ 195, § 199 BGB).</p>

<h2>§ 9 Schlussbestimmungen</h2>
<p>(1) Es gilt das Recht der Bundesrepublik Deutschland unter Ausschluss des UN-Kaufrechts. Gegenüber Verbrauchern gilt diese Rechtswahl nur insoweit, als dadurch zwingende Verbraucherschutzvorschriften des Staates, in dem der Verbraucher seinen gewöhnlichen Aufenthalt hat, nicht entzogen werden.</p>
<p>(2) Sofern der Kunde Kaufmann ist, sind der Erfüllungsort und der Gerichtsstand für alle Streitigkeiten zwischen uns und dem Kunden der Sitz der Burnout Celler-Kartbahn GmbH. Dasselbe gilt, wenn der Kunde keinen allgemeinen Gerichtsstand in Deutschland hat oder der Wohnsitz oder der gewöhnliche Aufenthalt im Zeitpunkt der Klageerhebung nicht bekannt sind.</p>
<p>(3) Abweichende Vereinbarungen oder Nebenabreden, die vor oder bei Vertragsschluss getroffen werden, bedürfen zu ihrer Wirksamkeit der Textform.</p>
<p>(4) Sollten einzelne Bestimmungen des Vertrages mit dem Kunden – einschließlich dieser Allgemeinen Geschäftsbedingungen – ganz oder teilweise unwirksam sein oder werden, so wird hierdurch die Gültigkeit der übrigen Bestimmungen nicht berührt.</p>
<p>(5) Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung bereit: <a href="https://ec.europa.eu/consumers/odr/" rel="noopener" target="_blank">ec.europa.eu/consumers/odr</a>. Wir sind nicht verpflichtet und nicht bereit, an einem Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>
<p class="small">Stand: Oktober 2026</p>
</div></section>
''' + footer() + end()
write("agb.html", html)

# ---------------- WIDERRUF ----------------
html = head("Widerrufsbelehrung | Burnout Celler-Kartbahn", "Widerrufsrecht für Verbraucher beim Online-Kauf von Gutscheinen der Burnout Celler-Kartbahn GmbH, Muster-Widerrufsformular und Hinweis zu terminierten Freizeitleistungen.", breadcrumb("Widerruf","widerruf.html")) + header()
html += f'''
<section class="section"><div class="wrap prose">
<h1>Widerrufsbelehrung</h1>
<p class="lead">Für Verbraucher beim Kauf von Gutscheinen über unsere Website (Fernabsatzvertrag).</p>

<h2>Widerrufsrecht</h2>
<p>Sie haben das Recht, binnen vierzehn Tagen ohne Angabe von Gründen diesen Vertrag zu widerrufen. Die Widerrufsfrist beträgt vierzehn Tage ab dem Tag des Vertragsabschlusses (bei Gutscheinen, die als Datei per E-Mail zugesandt werden) bzw. ab dem Tag, an dem Sie oder ein von Ihnen benannter Dritter, der nicht der Beförderer ist, den Gutschein in Besitz genommen haben (bei Versand oder Abholung eines Gutscheins in Papierform).</p>
<p>Um Ihr Widerrufsrecht auszuüben, müssen Sie uns, der Burnout Celler-Kartbahn GmbH, Waldweg 100, 29221 Celle, Telefon 05141 908650, E-Mail <a href="mailto:team@celler-kartbahn.com">team@celler-kartbahn.com</a>, mittels einer eindeutigen Erklärung (z.&nbsp;B. ein mit der Post versandter Brief oder eine E-Mail) über Ihren Entschluss, diesen Vertrag zu widerrufen, informieren. Sie können dafür das untenstehende Muster-Widerrufsformular verwenden, das jedoch nicht vorgeschrieben ist.</p>
<p>Zur Wahrung der Widerrufsfrist reicht es aus, dass Sie die Mitteilung über die Ausübung des Widerrufsrechts vor Ablauf der Widerrufsfrist absenden.</p>

<h2>Folgen des Widerrufs</h2>
<p>Wenn Sie diesen Vertrag widerrufen, haben wir Ihnen alle Zahlungen, die wir von Ihnen erhalten haben, einschließlich der Lieferkosten (mit Ausnahme der zusätzlichen Kosten, die sich daraus ergeben, dass Sie eine andere Art der Lieferung als die von uns angebotene, günstigste Standardlieferung gewählt haben), unverzüglich und spätestens binnen vierzehn Tagen ab dem Tag zurückzuzahlen, an dem die Mitteilung über Ihren Widerruf dieses Vertrags bei uns eingegangen ist. Für diese Rückzahlung verwenden wir dasselbe Zahlungsmittel, das Sie bei der ursprünglichen Transaktion eingesetzt haben, es sei denn, mit Ihnen wurde ausdrücklich etwas anderes vereinbart; in keinem Fall werden Ihnen wegen dieser Rückzahlung Entgelte berechnet. Ein bereits eingelöster Gutschein kann nicht widerrufen werden.</p>

<h2>Ausschluss des Widerrufsrechts</h2>
<p>Das Widerrufsrecht besteht nicht bei Verträgen zur Erbringung von Dienstleistungen im Zusammenhang mit Freizeitbetätigungen, wenn der Vertrag für die Erbringung einen spezifischen Termin oder Zeitraum vorsieht (§ 312g Abs. 2 Nr. 9 BGB). Das betrifft insbesondere Online-Buchungen von Ticketfahrten, Kidspartys, Rennen, Bahnmieten und Kursen zu einem festen Termin. Für diese Buchungen gelten die Stornierungsbedingungen in <a href="agb.html">§ 4 unserer AGB</a>.</p>

<h2>Muster-Widerrufsformular</h2>
<p>Wenn Sie den Vertrag widerrufen wollen, füllen Sie bitte dieses Formular aus und senden Sie es ab – oder schicken Sie uns den Text per Brief oder E-Mail.</p>
<form class="form" data-mk-form="widerruf" action="danke.html" method="post">
  <fieldset>
    <legend>Widerruf erklären</legend>
    <p>An Burnout Celler-Kartbahn GmbH, Waldweg 100, 29221 Celle, team@celler-kartbahn.com:<br>Hiermit widerrufe(n) ich/wir (*) den von mir/uns (*) abgeschlossenen Vertrag über den Kauf der folgenden Waren (*) / die Erbringung der folgenden Dienstleistung (*):</p>
    <div class="field"><label for="w-leistung">Bestellte Leistung (z.&nbsp;B. Gutschein 50 €) *</label><input type="text" id="w-leistung" name="leistung" required><span class="error"></span></div>
    <div class="fields-2">
      <div class="field"><label for="w-bestellt">Bestellt am *</label><input type="date" id="w-bestellt" name="bestellt_am" required><span class="error"></span></div>
      <div class="field"><label for="w-erhalten">Erhalten am</label><input type="date" id="w-erhalten" name="erhalten_am"></div>
    </div>
    <div class="field"><label for="w-ref">Vorgangs- oder Gutscheinnummer</label><input type="text" id="w-ref" name="vorgang"></div>
    <div class="field"><label for="w-name">Name des/der Verbraucher(s) *</label><input type="text" id="w-name" name="name" autocomplete="name" required><span class="error"></span></div>
    <div class="field"><label for="w-anschrift">Anschrift des/der Verbraucher(s) *</label><textarea id="w-anschrift" name="nachricht" required placeholder="Straße, PLZ, Ort"></textarea><span class="error"></span></div>
    <div class="fields-2">
      <div class="field"><label for="w-email">E-Mail *</label><input type="email" id="w-email" name="email" required><span class="error"></span></div>
      <div class="field"><label for="w-tel">Telefon</label><input type="tel" id="w-tel" name="telefon"></div>
    </div>
    <div class="field hp" aria-hidden="true"><label for="w-website">Website</label><input type="text" id="w-website" name="website" tabindex="-1" autocomplete="off"></div>
    <div class="field field--check"><input type="checkbox" id="w-einw" name="einwilligung" value="ja" required><label for="w-einw">Ich bin damit einverstanden, dass meine Angaben zur Bearbeitung des Widerrufs verarbeitet werden. Hinweise in der <a href="datenschutz.html">Datenschutzerklärung</a>. *</label><span class="error"></span></div>
    <div class="form-status" role="alert" aria-live="polite"></div>
    {fallback_box("Formular gerade nicht erreichbar? Widerruf per E-Mail oder Post senden:")}
    <button class="btn btn--primary" type="submit" style="margin-top:1rem">Widerruf absenden</button>
    <p class="small" style="margin-top:.6rem">(*) Unzutreffendes streichen. Datum: wird mit dem Absenden erfasst.</p>
  </fieldset>
</form>
</div></section>
''' + footer() + end()
write("widerruf.html", html)
