# -*- coding: utf-8 -*-
"""AGB mit Widerrufsbelehrung und Muster-Widerrufsformular sowie die Seite „Vertrag widerrufen“."""
import core
from core import ESC


def _anbieter(site):
    s = site.s
    a = s["address"]
    L = s["legal"]
    return f'{ESC(s["name"])}, Inhaber {ESC(L.get("owner", ""))}, {ESC(a["street"])}, {ESC(a["zip"])} {ESC(a["city"])}'


def build_agb(site, write):
    s = site.s
    a = s["address"]
    L = s["legal"]
    b = s.get("booking") or {}
    dep = b.get("depositPercent", 15)
    sc = b.get("conditionSurcharge") or {}
    pay = ", ".join(s.get("paymentMethods") or ["Bar", "Karte", "PayPal", "Überweisung"])
    anbieter = _anbieter(site)
    kontakt = f'Telefon {ESC(s["phoneIntl"])}, E-Mail <a href="mailto:{s["email"]}">{ESC(s["email"])}</a>'
    tax = ("Alle Preise sind Endpreise. Als Kleinunternehmer im Sinne von § 19 UStG berechnen wir keine Umsatzsteuer und weisen sie daher auch nicht aus."
           if L.get("smallBusiness") else "Alle Preise sind Endpreise inklusive der gesetzlichen Umsatzsteuer.")
    sur = ""
    if sc.get("percent"):
        tier = (sc.get("overrides") or {}).get("tierhaare")
        sur = (f" Für die bei der Buchung angegebenen Zustandsmerkmale erhöht sich der Richtpreis um je {sc['percent']} %"
               + (f", bei vielen Tierhaaren um {tier} %" if tier else "") + "; Ledersitze sind davon ausgenommen.")
    content = f'''
    <p>Diese Allgemeinen Geschäftsbedingungen gelten für alle Verträge über Leistungen der Fahrzeugaufbereitung und über Gutscheine zwischen {anbieter} (im Folgenden „ElbDetail“ oder „wir“) und unseren Kundinnen und Kunden (im Folgenden „Kunde“).</p>

    <h2 id="geltung">§ 1 Geltungsbereich</h2>
    <ol class="agb-list">
      <li>Diese AGB gelten für Verbraucher und Unternehmer. Verbraucher ist jede natürliche Person, die ein Rechtsgeschäft zu Zwecken abschließt, die überwiegend weder ihrer gewerblichen noch ihrer selbständigen beruflichen Tätigkeit zugerechnet werden können (§ 13 BGB).</li>
      <li>Abweichende Bedingungen des Kunden gelten nur, wenn wir ihnen ausdrücklich schriftlich zustimmen. Individuelle Absprachen haben Vorrang vor diesen AGB.</li>
    </ol>

    <h2 id="leistungen">§ 2 Leistungen</h2>
    <ol class="agb-list">
      <li>Wir bieten die Innen- und Außenaufbereitung von Fahrzeugen an, insbesondere Reinigung, Politur, Wachs- und Lackversiegelung, Keramikversiegelung (C²Coating) sowie Leder- und Innenraumpflege. Der Umfang ergibt sich aus dem gewählten Paket oder Angebot laut Website und aus der Absprache bei der Fahrzeugbesichtigung.</li>
      <li>Das Ergebnis hängt vom Ausgangszustand des Fahrzeugs ab. Eine Politur kann Kratzer, Hologramme und Waschspuren nur so weit entfernen, wie es die vorhandene Lackschicht zulässt. Tiefe Kratzer, Steinschläge, Lackschäden, alte Verfärbungen, Gerüche oder Flecken lassen sich nicht in jedem Fall vollständig beseitigen. Ein bestimmtes Ergebnis schulden wir nur, wenn es ausdrücklich vereinbart ist.</li>
      <li>Angaben zur Haltbarkeit von Versiegelungen und Keramikbeschichtungen sind Herstellerangaben unter optimalen Voraussetzungen. Die tatsächliche Haltbarkeit hängt von Beanspruchung, Witterung und Pflege ab und ist keine Garantie.</li>
      <li>Wir dürfen zur Leistungserbringung geeignete Hilfsmittel und Produkte nach eigener fachlicher Wahl einsetzen.</li>
    </ol>

    <h2 id="vertrag">§ 3 Vertragsschluss</h2>
    <ol class="agb-list">
      <li>Die Darstellung unserer Leistungen und Preise auf der Website ist kein verbindliches Angebot, sondern eine Einladung zur Buchung oder Anfrage.</li>
      <li><strong>Online-Buchung:</strong> Der Kunde wählt Leistung, Fahrzeugklasse, Tag und Abgabezeit und sendet die Buchung ab. Wir reservieren die Abgabezeit und senden dem Kunden per E-Mail einen Link. Über diesen Link bestätigt der Kunde die Buchung verbindlich, bei vereinbarter Anzahlung durch die Zahlung per PayPal. Mit dieser Bestätigung kommt der Vertrag zustande. Wird die Buchung nicht innerhalb der in der E-Mail genannten Frist bestätigt, verfällt die Reservierung.</li>
      <li><strong>Anfrage per Telefon, WhatsApp, E-Mail oder Formular:</strong> Der Vertrag kommt zustande, wenn wir den Termin bestätigen und der Kunde den Termin wahrnimmt oder die Bestätigung annimmt.</li>
      <li>Vertragssprache ist Deutsch. Die Angaben zur Buchung und diese AGB senden wir dem Kunden mit der Bestätigung per E-Mail. Die AGB sind außerdem jederzeit auf dieser Seite abrufbar.</li>
    </ol>

    <h2 id="preise">§ 4 Preise und Fahrzeugbesichtigung</h2>
    <ol class="agb-list">
      <li>Die Preise auf der Website sind Ab-Preise (Richtpreise) für Fahrzeuge in normalem Pflegezustand der jeweiligen Fahrzeugklasse.{sur} {tax}</li>
      <li>Vor Beginn der Arbeiten meldet sich {ESC((s.get("about") or {}).get("name") or "ElbDetail")} telefonisch und sieht sich das Fahrzeug an. Ergibt die Besichtigung einen höheren Aufwand als angegeben, nennen wir den verbindlichen Preis vor Arbeitsbeginn. Ist der Kunde damit nicht einverstanden, kann er vom Vertrag zurücktreten. Eine bereits geleistete Anzahlung erstatten wir in diesem Fall vollständig.</li>
      <li>Zusätzliche Leistungen, die über den vereinbarten Umfang hinausgehen, führen wir nur nach Absprache mit dem Kunden aus und berechnen sie nach Aufwand.</li>
    </ol>

    <h2 id="zahlung">§ 5 Anzahlung und Zahlung</h2>
    <ol class="agb-list">
      <li>Bei der Online-Buchung leistet der Kunde eine Anzahlung von {dep} % des Richtpreises per PayPal. Ist für eine Leistung kein fester Richtpreis hinterlegt, nennen wir die Höhe der Anzahlung vorab per E-Mail. Die Anzahlung wird mit dem Endpreis verrechnet.</li>
      <li>Der Restbetrag ist bei Abholung des Fahrzeugs fällig. Möglich sind: {ESC(pay)}. Gutscheine rechnen wir auf den Endpreis an.</li>
      <li>Uns steht wegen unserer Forderungen aus dem Vertrag ein Pfandrecht an dem Fahrzeug zu (§ 647 BGB), solange es sich in unserem Besitz befindet.</li>
    </ol>

    <h2 id="absage">§ 6 Verschieben, Absage und Ausfallpauschale</h2>
    <ol class="agb-list">
      <li>Der Kunde kann einen bestätigten Termin jederzeit kostenlos auf einen anderen freien Tag verschieben, über den Link in der Bestätigungs-E-Mail, telefonisch oder per WhatsApp. Eine geleistete Anzahlung bleibt dabei erhalten und wird auf den neuen Termin angerechnet.</li>
      <li>Das gesetzliche Widerrufsrecht für Verbraucher (§ 12 und Widerrufsbelehrung) bleibt unberührt. Sagt der Kunde den Termin innerhalb der Widerrufsfrist ab, behandeln wir die Absage als Widerruf und erstatten die Anzahlung vollständig.</li>
      <li>Sagt der Kunde einen bestätigten Termin nach Ablauf der Widerrufsfrist ab oder erscheint er ohne Absage nicht, behalten wir die Anzahlung als pauschalen Ersatz für den freigehaltenen Termin ein. Dem Kunden bleibt der Nachweis gestattet, dass uns kein oder ein wesentlich geringerer Schaden entstanden ist. In diesem Fall erstatten wir den Unterschied.</li>
      <li>Müssen wir einen Termin absagen, zum Beispiel wegen Krankheit, bieten wir einen Ersatztermin an. Wünscht der Kunde keinen Ersatztermin, erstatten wir die Anzahlung vollständig.</li>
    </ol>

    <h2 id="uebergabe">§ 7 Fahrzeugübergabe und Mitwirkung des Kunden</h2>
    <ol class="agb-list">
      <li>Der Kunde bringt das Fahrzeug zur vereinbarten Abgabezeit an unseren Standort {ESC(a["street"])}, {ESC(a["zip"])} {ESC(a["city"])}, sofern kein Hol- und Bringservice vereinbart ist. Bei Versiegelung und Keramik bleibt das Fahrzeug in der Regel 3 Tage bei uns, bei anderen Leistungen nach Möglichkeit einen Tag.</li>
      <li>Der Kunde entfernt vor der Übergabe Wertsachen und persönliche Gegenstände aus dem Fahrzeug.</li>
      <li>Der Kunde weist uns vor Beginn auf ihm bekannte Vorschäden und Besonderheiten hin, zum Beispiel Nachlackierungen, Smart-Repair-Stellen, Folierungen, lose Teile, empfindliche Materialien oder Undichtigkeiten.</li>
      <li>Bei der Übergabe sehen wir uns das Fahrzeug gemeinsam an und halten sichtbare Vorschäden auf Wunsch mit Fotos fest.</li>
    </ol>

    <h2 id="abholung">§ 8 Abholung</h2>
    <p>Wir informieren den Kunden, sobald das Fahrzeug fertig ist. Der Kunde holt das Fahrzeug zum vereinbarten Zeitpunkt ab. Eine längere Standzeit stimmen wir gern vorher ab.</p>

    <h2 id="maengel">§ 9 Mängelrechte</h2>
    <ol class="agb-list">
      <li>Es gelten die gesetzlichen Mängelrechte.</li>
      <li>Wir bitten den Kunden, das Fahrzeug bei der Abholung anzusehen und Beanstandungen möglichst gleich oder zeitnah zu melden. So können wir schnell nachbessern. Die gesetzlichen Rechte des Kunden bleiben davon unberührt.</li>
      <li>Für die Haltbarkeit einer Versiegelung oder Keramikbeschichtung sind die Pflegehinweise wichtig, die wir bei der Abholung mitgeben.</li>
    </ol>

    <h2 id="haftung">§ 10 Haftung</h2>
    <ol class="agb-list">
      <li>Wir haften unbeschränkt bei Vorsatz und grober Fahrlässigkeit, bei der Verletzung von Leben, Körper oder Gesundheit sowie nach dem Produkthaftungsgesetz.</li>
      <li>Bei leichter Fahrlässigkeit haften wir nur bei Verletzung einer wesentlichen Vertragspflicht, deren Erfüllung die ordnungsgemäße Durchführung des Vertrags überhaupt erst ermöglicht und auf deren Einhaltung der Kunde regelmäßig vertrauen darf. In diesem Fall ist die Haftung auf den vorhersehbaren, vertragstypischen Schaden begrenzt.</li>
      <li>Wir haften nicht für Schäden, die auf Vorschäden oder Mängel des Fahrzeugs zurückgehen, die bei fachgerechter Arbeit nicht erkennbar waren, zum Beispiel lose oder mangelhafte Nachlackierungen, Rost unter dem Lack oder poröse Dichtungen, es sei denn, wir haben den Schaden zu vertreten.</li>
    </ol>

    <h2 id="gutscheine">§ 11 Gutscheine</h2>
    <ol class="agb-list">
      <li>Gutscheine sind drei Jahre gültig, gerechnet ab dem Ende des Jahres, in dem sie gekauft wurden.</li>
      <li>Wertgutscheine können für alle unsere Leistungen eingelöst werden, auch in Teilbeträgen. Ein Restguthaben bleibt bis zum Ende der Gültigkeit erhalten. Paketgutscheine gelten für das genannte Paket für einen Kleinwagen; bei größeren Fahrzeugen zahlt der Kunde nur die Differenz.</li>
      <li>Gutscheine sind übertragbar. Eine Barauszahlung ist ausgeschlossen, soweit das Gesetz nichts anderes vorsieht.</li>
      <li>Nach der Bestellung erhält der Kunde die Zahlungsdaten per E-Mail. Den Gutschein senden wir nach Zahlungseingang.</li>
    </ol>

    <h2 id="widerrufsrecht">§ 12 Widerrufsrecht</h2>
    <p>Verbrauchern steht bei Verträgen, die ausschließlich über Fernkommunikationsmittel geschlossen werden (zum Beispiel über die Website, per E-Mail, Telefon oder WhatsApp), ein Widerrufsrecht nach Maßgabe der folgenden Widerrufsbelehrung zu. Den Widerruf können Sie einfach über die Funktion <a href="widerruf.html">„Vertrag widerrufen“</a> auf unserer Website erklären.</p>

    <h2 id="streit">§ 13 Streitbeilegung</h2>
    <p>Wir sind nicht verpflichtet und nicht bereit, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.</p>

    <h2 id="schluss">§ 14 Schlussbestimmungen</h2>
    <ol class="agb-list">
      <li>Es gilt das Recht der Bundesrepublik Deutschland. Bei Verbrauchern gilt diese Rechtswahl nur, soweit dadurch nicht der Schutz durch zwingende Vorschriften des Staates entzogen wird, in dem der Verbraucher seinen gewöhnlichen Aufenthalt hat.</li>
      <li>Ist der Kunde Kaufmann, juristische Person des öffentlichen Rechts oder öffentlich-rechtliches Sondervermögen, ist Gerichtsstand {ESC(a["city"])}.</li>
      <li>Sollten einzelne Bestimmungen dieser AGB unwirksam sein, bleibt die Wirksamkeit der übrigen Bestimmungen unberührt.</li>
    </ol>

    <h2 id="widerruf">Widerrufsbelehrung</h2>
    <div class="legal-box">
      <h3>Widerrufsrecht</h3>
      <p>Sie haben das Recht, binnen vierzehn Tagen ohne Angabe von Gründen diesen Vertrag zu widerrufen. Die Widerrufsfrist beträgt vierzehn Tage ab dem Tag des Vertragsabschlusses.</p>
      <p>Um Ihr Widerrufsrecht auszuüben, müssen Sie uns ({anbieter}, {kontakt}) mittels einer eindeutigen Erklärung (z. B. ein mit der Post versandter Brief oder eine E-Mail) über Ihren Entschluss, diesen Vertrag zu widerrufen, informieren. Sie können dafür auch die Funktion <a href="widerruf.html">„Vertrag widerrufen“</a> auf unserer Website nutzen. Sie können dafür das beigefügte Muster-Widerrufsformular verwenden, das jedoch nicht vorgeschrieben ist.</p>
      <p>Zur Wahrung der Widerrufsfrist reicht es aus, dass Sie die Mitteilung über die Ausübung des Widerrufsrechts vor Ablauf der Widerrufsfrist absenden.</p>
      <h3>Folgen des Widerrufs</h3>
      <p>Wenn Sie diesen Vertrag widerrufen, haben wir Ihnen alle Zahlungen, die wir von Ihnen erhalten haben, unverzüglich und spätestens binnen vierzehn Tagen ab dem Tag zurückzuzahlen, an dem die Mitteilung über Ihren Widerruf dieses Vertrags bei uns eingegangen ist. Für diese Rückzahlung verwenden wir dasselbe Zahlungsmittel, das Sie bei der ursprünglichen Transaktion eingesetzt haben, es sei denn, mit Ihnen wurde ausdrücklich etwas anderes vereinbart; in keinem Fall werden Ihnen wegen dieser Rückzahlung Entgelte berechnet.</p>
      <p>Haben Sie verlangt, dass die Dienstleistungen während der Widerrufsfrist beginnen sollen, so haben Sie uns einen angemessenen Betrag zu zahlen, der dem Anteil der bis zu dem Zeitpunkt, zu dem Sie uns von der Ausübung des Widerrufsrechts hinsichtlich dieses Vertrags unterrichten, bereits erbrachten Dienstleistungen im Vergleich zum Gesamtumfang der im Vertrag vorgesehenen Dienstleistungen entspricht.</p>
      <h3>Hinweis zum Erlöschen des Widerrufsrechts</h3>
      <p>Das Widerrufsrecht erlischt bei einem Vertrag zur Erbringung von Dienstleistungen, wenn wir die Dienstleistung vollständig erbracht haben und mit der Ausführung erst begonnen haben, nachdem Sie dazu Ihre ausdrückliche Zustimmung gegeben und gleichzeitig Ihre Kenntnis davon bestätigt haben, dass Sie Ihr Widerrufsrecht bei vollständiger Vertragserfüllung durch uns verlieren.</p>
    </div>

    <h2 id="widerrufsformular">Muster-Widerrufsformular</h2>
    <div class="legal-box">
      <p>(Wenn Sie den Vertrag widerrufen wollen, dann füllen Sie bitte dieses Formular aus und senden Sie es zurück. Einfacher geht es über <a href="widerruf.html">„Vertrag widerrufen“</a>.)</p>
      <p>An {anbieter}, E-Mail {ESC(s["email"])}:</p>
      <p>Hiermit widerrufe(n) ich/wir (*) den von mir/uns (*) abgeschlossenen Vertrag über den Kauf der folgenden Waren (*)/die Erbringung der folgenden Dienstleistung (*)</p>
      <p>– Bestellt am (*)/erhalten am (*)<br>– Name des/der Verbraucher(s)<br>– Anschrift des/der Verbraucher(s)<br>– Unterschrift des/der Verbraucher(s) (nur bei Mitteilung auf Papier)<br>– Datum</p>
      <p>(*) Unzutreffendes streichen.</p>
    </div>
'''
    _page(site, write, "agb.html", "AGB und Widerrufsbelehrung | ElbDetail Celle",
          "Allgemeine Geschäftsbedingungen von ElbDetail, Fahrzeugaufbereitung in Celle: Buchung, Anzahlung, Absage, Haftung, Gutscheine und Widerrufsbelehrung.",
          "Allgemeine Geschäfts&shy;bedingungen", f"Stand: {s['stand']}", content)


def build_widerruf(site, write):
    s = site.s
    content = f'''
    <p>Sie möchten einen Vertrag mit uns widerrufen, zum Beispiel eine Online-Buchung oder eine Gutscheinbestellung? Füllen Sie das Formular aus und klicken Sie auf „Widerruf bestätigen“. Sie erhalten sofort eine Eingangsbestätigung per E-Mail.</p>
    <p><strong>Termin online gebucht?</strong> Dann geht es noch einfacher: Öffnen Sie den Link „Vertrag widerrufen“ in Ihrer Bestätigungs-E-Mail und klicken Sie auf „Widerruf bestätigen“. Sie müssen nichts ausfüllen. Alle Infos zu Fristen und Folgen stehen in der <a href="agb.html#widerruf">Widerrufsbelehrung</a>.</p>
    <form class="widerruf-form js-form" id="widerrufForm" data-form="widerruf" action="/api/anfrage" method="post" novalidate>
      <input type="hidden" name="typ" value="widerruf">
      <div class="form-row"><label for="w-name">Ihr Name*</label><input type="text" id="w-name" name="name" autocomplete="name" required maxlength="120"></div>
      <div class="form-row"><label for="w-email">E-Mail* <span class="hint">(für die Eingangsbestätigung)</span></label><input type="email" id="w-email" name="email" autocomplete="email" required maxlength="160"></div>
      <div class="form-row"><label for="w-vorgang">Vorgangsnummer oder Gutscheincode* <span class="hint">(steht in Ihrer E-Mail, z. B. T261021-AB12)</span></label><input type="text" id="w-vorgang" name="vorgang" required maxlength="40" autocapitalize="characters"></div>
      <div class="form-row"><label for="w-msg">Welcher Vertrag, bestellt am <span class="hint">(optional)</span></label><textarea id="w-msg" name="nachricht" rows="3" maxlength="2000" placeholder="z. B. Termin am 12.11. oder Gutschein über 100 €"></textarea></div>
      {core.honeypot("w-website")}
      <p class="form-note" style="margin-left:0">Ihre Angaben verwenden wir nur, um den Widerruf zu bearbeiten (Art. 6 Abs. 1 lit. c DSGVO). Mehr in der <a href="datenschutz.html">Datenschutzerklärung</a>.</p>
      <button class="btn btn-primary" type="submit">Widerruf bestätigen</button>
      {core.form_status("w-status")}
    </form>
    <p>Sie können den Widerruf auch per E-Mail an <a href="mailto:{s["email"]}">{ESC(s["email"])}</a> oder per Brief erklären.</p>
'''
    _page(site, write, "widerruf.html", "Vertrag widerrufen | ElbDetail Celle",
          "Vertrag mit ElbDetail widerrufen: Online-Buchung oder Gutschein einfach per Formular widerrufen und sofort eine Eingangsbestätigung erhalten.",
          "Vertrag widerrufen", "Widerruf einer Buchung oder Gutscheinbestellung", content, noindex=True)


def _page(site, write, fname, title, desc, h1, sub, content, noindex=False):
    body = f'''
<main id="main" class="legal-main">
  <div class="container">
    <a class="back-home" href="index.html">&larr; Zurück zur Startseite</a>
    <h1>{h1}</h1>
    <p class="legal-updated">{sub}</p>
    {content}
  </div>
</main>
'''
    write(fname, core.head(site, title, desc, "/" + fname, noindex=noindex) + core.header(site) + body + core.footer(site))
