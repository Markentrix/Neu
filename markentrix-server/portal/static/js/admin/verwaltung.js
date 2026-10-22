import { leistungstextKarte } from './angebotsplus.js';
import { h, api, datum, zeit, euro, melde, formular, dialog } from '../common.js';
import { V, bestaetigt, cent, fehler, feld, fmtEuro, knopf, kopf, pill, tabelle } from './kern.js';

V.katalog = async () => {
  const d = await api('/api/admin/katalog');
  return h('div', { class: 'stack' }, kopf('Pakete & Preise'),
    h('div', { class: 'card' }, h('h2', {}, 'Produkte (aktuelle Preise)'),
      tabelle([['Code', z => z.code], ['Name', z => z.name], ['Einrichtung', z => euro(z.einrichtung_cent)], ['Monatlich', z => euro(z.monatlich_cent)], ['Projekt', z => euro(z.projekt_cent)]], d.produkte)),
    h('div', { class: 'card' }, h('h2', {}, 'Module'), tabelle([['Code', z => z.code], ['Name', z => z.name], ['Art', z => z.art], ['Beschreibung', z => z.beschreibung]], d.module)),
    h('p', { class: 'muted small' }, 'Preise ändern: neue Zeile in produkt_preise mit späterem gueltig_ab (mkctl psql). Bestehende Buchungen behalten ihren Preis.'));
};

/** Website als ZIP hochladen und veröffentlichen. Der Server prüft die ZIP, richtet Domain und HTTPS ein und sichert die vorige Version. */
const dnsBox = h('div');
const checkZeigen = (r, titel) => {
  const farbe = { gruen: 'ok', gelb: 'warn', rot: 'bad' }[r.ampel];
  dnsBox.replaceChildren(h('div', { class: 'card' }, h('h2', {}, 'Livegang-Check: ' + titel),
    h('p', {}, h('span', { class: 'pill ' + farbe }, { gruen: 'bereit', gelb: 'mit Hinweisen', rot: 'Fehler gefunden' }[r.ampel]), ' ' + r.seiten + ' Seiten geprüft'),
    r.punkte.length ? h('ul', {}, ...r.punkte.map(x => h('li', {}, h('span', { class: 'pill ' + ({ fehler: 'bad', warn: 'warn', hinweis: '' }[x.stufe]) }, { fehler: 'Fehler', warn: 'Warnung', hinweis: 'Hinweis' }[x.stufe]), ' ' + x.text + (x.ort ? ' (' + x.ort + ')' : '')))) : h('p', {}, 'Keine Auffälligkeiten.')));
  dnsBox.scrollIntoView({ behavior: 'smooth' });
};

const dnsZeigen = (r) => {
  dnsBox.replaceChildren(h('div', { class: 'card' }, h('h2', {}, 'DNS-Prüfung: ' + r.domain),
    h('p', {}, h('span', { class: 'pill ' + (r.ok ? 'ok' : 'bad') }, r.ok ? 'zeigt auf diesen Server' : 'noch nicht umgestellt'), r.dns_anbieter ? ' DNS bei: ' + r.dns_anbieter : ''),
    h('table', { class: 'tbl' }, h('tbody', {}, ...[r.apex, r.www].map(x => h('tr', {}, h('td', {}, x.name), h('td', {}, (x.a.join(', ') || '–') + (x.aaaa.length ? ' · AAAA ' + x.aaaa.join(', ') : '')), h('td', {}, h('span', { class: 'pill ' + (x.status === 'ok' ? 'ok' : 'bad') }, x.status)))))),
    r.probleme.length ? h('ul', {}, ...r.probleme.map(t => h('li', {}, t))) : '',
    r.schritte.length ? h('ol', {}, ...r.schritte.map(t => h('li', {}, t))) : '',
    r.kundentext ? h('div', {}, h('h3', {}, 'Text für den Kunden'), h('textarea', { rows: 12, style: 'width:100%', readonly: true }, r.kundentext),
      h('button', { class: 'btn small sec', onclick: (ev) => navigator.clipboard.writeText(r.kundentext).then(() => { ev.target.textContent = 'Kopiert ✓'; }) }, 'Text kopieren'), ' ',
      h('button', { class: 'btn small', onclick: async (ev) => {
        if (!confirm('Die Anleitung jetzt per E-Mail an den Kunden schicken? In 3 Tagen kommt automatisch eine Erinnerung, falls die Domain dann noch nicht stimmt.')) return;
        ev.target.disabled = true;
        try { const a = await api('/api/admin/websites/domain/' + encodeURIComponent(r.domain) + '/kundenmail', { method: 'POST' }); ev.target.textContent = 'Gesendet ✓'; ev.target.parentNode.append(h('p', { class: 'small' }, a.hinweis)); }
        catch (x) { ev.target.disabled = false; ev.target.parentNode.append(h('p', { class: 'small', style: 'color:var(--bad,#e66)' }, x.message)); }
      } }, 'An Kunden mailen'),
      r.kundenmail_am ? h('p', { class: 'small muted' }, 'Zuletzt gesendet am ' + datum(r.kundenmail_am) + (r.erinnerungen ? ' · ' + r.erinnerungen + ' Erinnerung(en) verschickt' : '')) : '') : '',
    h('p', { class: 'small muted' }, 'Server-Adresse: ' + (r.server_ipv4.join(', ') || 'unbekannt'))));
  dnsBox.scrollIntoView({ behavior: 'smooth' });
};

async function statusKarte() {
  const m = h('div'), box = h('div');
  const art = h('select', {}, [['stoerung', 'Störung'], ['wartung', 'Wartung'], ['info', 'Hinweis']].map(([v, t]) => h('option', { value: v }, t)));
  const titel = h('input', { placeholder: 'Kurzer Titel, z. B. „Wartung am Sonntag“', maxlength: 120 });
  const text = h('textarea', { rows: 2, maxlength: 1500, placeholder: 'Was ist los, was bedeutet das für Kunden?' });
  const laden = async () => {
    const l = await api('/api/admin/statusmeldungen');
    box.replaceChildren(tabelle([['Art', z => ({ stoerung: 'Störung', wartung: 'Wartung', info: 'Hinweis' })[z.art]], ['Titel', z => z.titel], ['Seit', z => zeit(z.beginn)], ['Stand', z => z.beendet_am ? 'beendet ' + zeit(z.beendet_am) : h('span', { class: 'pill warn' }, 'aktiv')],
      ['', z => z.beendet_am ? '' : knopf('Beenden', async () => { try { await api('/api/admin/statusmeldungen/' + z.id + '/beenden', { method: 'POST' }); laden(); } catch (x) { melde(m, x.message); } }, 'sec small')]], l.slice(0, 8), 'Keine Meldungen.'));
  };
  setTimeout(laden, 0);
  const url = location.origin + '/status';
  return h('div', { class: 'card' }, h('h2', {}, 'Statusseite'), h('p', { class: 'small muted' }, 'Für angemeldete Kunden, Vertriebler und dein Team (Link steht in der Fußzeile jedes Portals): ', h('a', { href: '/status', target: '_blank' }, url), '. Zeigt Portal, Datenbank, Websites (nur Zahlen), E-Mail und Sicherung automatisch. Hier trägst du Störungen und Wartung ein, damit Kunden nicht anrufen müssen.'), m,
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Art'), art), h('div', {}, h('label', {}, 'Titel'), titel)), h('label', {}, 'Text (optional)'), text,
    h('p', {}, knopf('Meldung veröffentlichen', async () => { if (!titel.value.trim()) { melde(m, 'Bitte einen Titel eintragen.'); return; } try { await api('/api/admin/statusmeldungen', { method: 'POST', body: { art: art.value, titel: titel.value, text: text.value } }); titel.value = ''; text.value = ''; melde(m, 'Veröffentlicht.', 'ok'); laden(); } catch (x) { melde(m, x.message); } }, '')), box);
}

async function uploadKarte(d) {
  const kunden = await api('/api/admin/kunden'), m = h('div'), verlauf = h('div');
  const art = h('select', {}, [['live', 'Live-Website (eigene Domain)'], ['demo', 'Demo (demo.markentrix.de/name)']].map(([v, t]) => h('option', { value: v }, t)));
  const name = h('input', { placeholder: 'Domain ohne www, z. B. elbdetail.de', maxlength: 253, autocomplete: 'off' });
  const kunde = h('select', {}, [h('option', { value: '' }, '– Kunde wählen –')].concat(kunden.map(k => h('option', { value: k.id, 'data-domain': k.domain || '' }, k.kundennummer + ' · ' + k.firma))));
  const datei = h('input', { type: 'file', accept: '.zip,application/zip', multiple: true });
  const skript = h('input', { type: 'checkbox', style: 'width:auto', checked: true });
  const knopfHoch = h('button', { class: 'btn', type: 'button' }, 'Hochladen und veröffentlichen');
  art.addEventListener('change', () => { name.placeholder = art.value === 'live' ? 'Domain ohne www, z. B. elbdetail.de' : 'Name der Demo, z. B. anadolu'; });
  kunde.addEventListener('change', () => { const dom = (kunde.selectedOptions[0].getAttribute('data-domain') || '').replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/\/.*$/, ''); if (dom && !name.value && art.value === 'live') name.value = dom; });
  // bekannte Live-Seiten: Name vorschlagen und Kunde vorbelegen
  const bekannt = d.aktiv.filter(z => z.art === 'live');
  const liste = h('datalist', { id: 'bekannte-seiten' }, bekannt.map(z => h('option', { value: z.name })));
  name.setAttribute('list', 'bekannte-seiten');
  const weg = () => { try { return JSON.parse(localStorage.getItem('mk_upload_weg') || '[]'); } catch { return []; } };
  const wegMerken = (id) => { try { localStorage.setItem('mk_upload_weg', JSON.stringify(weg().concat(id).slice(-200))); } catch { /* nur Komfort */ } };
  const dnsHinweis = async (e, box) => {
    // Neue Live-Website: zeigt die Domain schon auf den Server? Wenn nicht, steht hier genau, was einzutragen ist.
    try {
      const r = await api('/api/admin/websites/domain/' + encodeURIComponent(e.name));
      if (r.ok) { box.replaceChildren(h('span', {}, 'Veröffentlicht, Domain zeigt auf diesen Server. ', h('a', { href: e.url, target: '_blank', rel: 'noopener' }, 'Seite öffnen'))); return; }
      box.replaceChildren(h('div', {}, h('b', {}, e.name + ': '), 'Veröffentlicht, aber die Domain zeigt noch nicht auf diesen Server. ', h('a', { href: e.url, target: '_blank', rel: 'noopener' }, 'Seite öffnen'), h('div', {}, 'So geht es:'),
        r.schritte.length ? h('ol', { style: 'margin:6px 0 0 18px' }, ...r.schritte.map(t => h('li', {}, t))) : '',
        h('div', { class: 'small', style: 'margin-top:6px' }, 'Server-Adresse: ' + (r.server_ipv4.join(', ') || 'unbekannt') + ' · ', h('a', { href: e.url, target: '_blank', rel: 'noopener' }, 'Seite öffnen'), ' · ', h('a', { href: '#', onclick: (ev) => { ev.preventDefault(); dnsZeigen(r); } }, 'Genaue DNS-Prüfung mit Text für den Kunden'))));
    } catch { /* Hinweis ist nur eine Hilfe */ }
  };
  const ladeVerlauf = async () => {
    try {
      const v = await api('/api/admin/websites/veroeffentlichungen');
      const gesehen = new Set(), ausgeblendet = weg();
      const neueste = v.ergebnisse.filter(e => { const k = e.art + '|' + e.name; if (gesehen.has(k)) return false; gesehen.add(k); return !ausgeblendet.includes(e.id); }).slice(0, 4);
      verlauf.replaceChildren(
        v.offen.length ? h('p', { class: 'small' }, h('span', { class: 'pill warn' }, 'läuft'), ' ' + v.offen.map(o => o.name).join(', ') + ' wird gerade veröffentlicht (bis zu einer Minute).') : '',
        ...neueste.map(e => {
          const text = h('div', { style: 'flex:1' }, h('b', {}, e.name + ': '), e.neu && e.art === 'live' && e.ok ? 'Veröffentlicht. Prüfe die Domain …' : e.text + ' ', e.ok && e.url ? h('a', { href: e.url, target: '_blank', rel: 'noopener' }, 'Seite öffnen') : '');
          if (e.ok && e.neu && e.art === 'live') dnsHinweis(e, text);
          return h('div', { class: 'msg ' + (e.ok ? 'ok' : 'err'), style: 'margin:6px 0;display:flex;gap:10px;align-items:flex-start' }, text,
            h('button', { class: 'btn small sec', type: 'button', title: 'Meldung ausblenden', onclick: (ev) => { wegMerken(e.id); ev.target.closest('.msg').remove(); } }, '×'));
        }));
      if (v.offen.length) setTimeout(ladeVerlauf, 5000);
    } catch { /* Anzeige ist nur eine Hilfe */ }
  };
  knopfHoch.addEventListener('click', async () => {
    melde(m, '');
    if (!datei.files.length) { melde(m, 'Bitte eine ZIP-Datei wählen.'); return; }
    const f = new FormData(); for (const x of datei.files) f.append('datei', x); f.append('art', art.value); f.append('name', name.value); f.append('kunden_id', kunde.value); f.append('dienste_skript', skript.checked ? '1' : '0');
    knopfHoch.disabled = true; knopfHoch.textContent = 'Lade hoch …';
    try { const r = await api('/api/admin/websites/upload', { method: 'POST', body: f }); melde(m, r.hinweis + ' (' + r.dateien + ' Dateien aus „' + r.ordner + '“' + (r.skript_in_seiten ? ', Website-Dienste in ' + r.skript_in_seiten + ' Seiten eingebaut' : '') + ')', 'ok'); if (r.check) checkZeigen(r.check, name.value); datei.value = ''; setTimeout(ladeVerlauf, 1500); }
    catch (x) { melde(m, x.message); }
    knopfHoch.disabled = false; knopfHoch.textContent = 'Hochladen und veröffentlichen';
  });
  const zurueckKnopf = h('button', { class: 'btn sec', type: 'button', onclick: async () => {
    if (!name.value) { melde(m, 'Bitte oben den Namen der Seite eintragen.'); return; }
    if (!confirm('Die vorige Version von ' + name.value + ' wieder online stellen?')) return;
    try { const r = await api('/api/admin/websites/zurueck', { method: 'POST', body: { art: art.value, name: name.value } }); melde(m, r.hinweis, 'ok'); setTimeout(ladeVerlauf, 1500); } catch (x) { melde(m, x.message); }
  } }, 'Vorige Version zurückholen');
  setTimeout(ladeVerlauf, 0);
  const f = (t, el, tipp) => h('div', {}, h('label', {}, t), el, tipp ? h('div', { class: 'small muted' }, tipp) : '');
  return h('div', { class: 'card' }, h('h2', {}, 'Website hochladen'),
    h('p', { class: 'small muted' }, 'Die fertige Website als ZIP (die index.html direkt oben). Besteht sie aus mehreren Teilen (z. B. Zip 1 = Seiten, Zip 2 = Bilder), alle ZIPs gleichzeitig auswählen: Sie werden in dieser Reihenfolge zusammengeführt, spätere ersetzen gleichnamige Dateien. Der Server prüft die Dateien, richtet bei einer neuen Domain Website und HTTPS selbst ein und sichert die vorige Version. Erneutes Hochladen mit demselben Namen aktualisiert die Seite.'),
    m, liste, h('div', { class: 'form2' }, f('Art', art), f('Name / Domain', name, 'Bei bestehenden Seiten wird der Name vorgeschlagen.'), f('Kunde (Kundennummer)', kunde, 'Bei neuen Live-Websites nötig. Die Domain des Kunden wird vorgeschlagen.'), f('ZIP-Datei', datei, 'Bis 120 MB.')),
    h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;margin-top:8px' }, skript, 'Website-Dienste (Formular, Termine, Statistik) automatisch in alle Seiten einbauen'),
    h('div', { class: 'row', style: 'margin-top:10px' }, knopfHoch, zurueckKnopf), verlauf);
}

/** Kunde sieht die Demo, gibt per Klick frei – Name, Zeit und Version werden festgehalten. */
async function vorschauKarte(d) {
  const demos = d.aktiv.filter(z => z.art === 'demo');
  if (!demos.length) return '';
  const kunden = await api('/api/admin/kunden'), m = h('div');
  const demo = h('select', {}, demos.map(z => h('option', { value: z.name }, z.name + (z.freigabe ? ' (' + z.freigabe.status + ')' : ''))));
  const kunde = h('select', {}, [h('option', { value: '' }, '– Kunde wählen –')].concat(kunden.map(k => h('option', { value: k.id }, k.kundennummer + ' · ' + k.firma))));
  const hinweis = h('input', { placeholder: 'Kurzer Satz für die Mail (optional)', maxlength: 500 });
  const los = h('button', { class: 'btn', type: 'button', onclick: async () => {
    if (!kunde.value) { melde(m, 'Bitte den Kunden wählen.'); return; }
    if (!confirm('Dem Kunden die Vorschau „' + demo.value + '“ zur Freigabe schicken?')) return;
    try { await api('/api/admin/websites/vorschau-freigabe', { method: 'POST', body: { kunden_id: kunde.value, demo_name: demo.value, hinweis: hinweis.value } }); melde(m, 'Gesendet. Der Kunde bekommt eine E-Mail mit Link; seine Entscheidung steht danach hier und unter Freigaben.', 'ok'); setTimeout(() => location.reload(), 2500); }
    catch (x) { melde(m, x.message); }
  } }, 'Vorschau zur Freigabe schicken');
  const f = (t, el) => h('div', {}, h('label', {}, t), el);
  return h('div', { class: 'card' }, h('h2', {}, 'Vorschau vom Kunden freigeben lassen'),
    h('p', { class: 'small muted' }, 'Der Kunde öffnet die Demo und bestätigt mit einem Klick (ohne Anmeldung, Link 14 Tage gültig). Freigabe oder Änderungswunsch wird mit Namen und Zeit festgehalten.'),
    m, h('div', { class: 'form2' }, f('Demo', demo), f('Kunde', kunde), f('Hinweis', hinweis)), h('div', { class: 'row', style: 'margin-top:10px' }, los));
}

/** Eine Seite aus der nächtlichen Sicherung zurückholen (die jetzige Version bleibt als Vorversion erhalten). */
async function sicherungKarte(d) {
  const sich = await api('/api/admin/websites/sicherungen'), m = h('div');
  const namen = d.aktiv.map(z => z.art + ':' + z.name);
  const seite = h('select', {}, namen.map(n => h('option', { value: n }, (n.startsWith('live') ? 'Live · ' : 'Demo · ') + n.split(':')[1])));
  const tag = h('select', {}, sich.tage.map(t => h('option', { value: t }, t.slice(8, 10) + '.' + t.slice(5, 7) + '.' + t.slice(0, 4) + ' ' + t.slice(11, 13) + ':' + t.slice(13))));
  const los = h('button', { class: 'btn sec', type: 'button', onclick: async () => {
    if (!seite.value || !tag.value) return;
    const [art, name] = seite.value.split(':');
    if (!confirm(name + ' aus der Sicherung vom ' + tag.selectedOptions[0].textContent + ' holen?\nDie jetzige Version bleibt als Vorversion erhalten.')) return;
    try { const r = await api('/api/admin/websites/aus-sicherung', { method: 'POST', body: { art, name, tag: tag.value } }); melde(m, r.hinweis, 'ok'); } catch (x) { melde(m, x.message); }
  } }, 'Aus Sicherung holen');
  const f = (t, el) => h('div', {}, h('label', {}, t), el);
  return h('div', { class: 'card' }, h('h2', {}, 'Aus Tagessicherung wiederherstellen'),
    h('p', { class: 'small muted' }, 'Holt die Dateien einer Website aus der nächtlichen Sicherung zurück. Termine, Anfragen und Einstellungen in der Datenbank werden dabei nicht verändert.'),
    m, sich.tage.length && namen.length ? [h('div', { class: 'form2' }, f('Seite', seite), f('Sicherung vom', tag)), h('div', { class: 'row', style: 'margin-top:10px' }, los)] : h('p', { class: 'small muted' }, 'Noch keine Sicherung vorhanden (die erste entsteht nachts).'));
}

V.websites = async () => {
  dnsBox.replaceChildren();
  const d = await api('/api/admin/websites');
  const m = h('div');
  const mb = (b) => b > 1048576 ? (b / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1024)) + ' KB';
  const wann = (t) => new Date(t * 1000).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' });
  const loesch = (z) => z.loeschung_laeuft ? h('span', { class: 'pill warn' }, 'wird gelöscht …') :
    h('button', { class: 'btn small bad', onclick: async () => {
      const eingabe = prompt('Zum Löschen den Namen genau eintippen:\n' + z.name + '\n\nDie Seite geht offline und liegt ' + d.aufbewahrung_tage + ' Tage im Papierkorb.');
      if (eingabe === null) return;
      try { const r = await api('/api/admin/websites/loeschen', { method: 'POST', body: { art: z.art, name: z.name, bestaetigung: eingabe } }); melde(m, r.hinweis, 'ok'); setTimeout(() => location.reload(), 1500); }
      catch (x) { melde(m, x.message); }
    } }, 'Löschen');
  /** Demo mit einem Klick als Live-Website auf die Kundendomain legen (Check, Sicherung, Webserver und Zertifikat laufen wie beim Upload). */
  const liveKnopf = (z) => z.art !== 'demo' ? '' : h('button', { class: 'btn small', title: 'Diese Demo als Live-Website veröffentlichen', onclick: async () => {
    const kunden = await api('/api/admin/kunden'), dm = h('div');
    const nr = (z.kunde || '').split(' ')[0].toUpperCase();
    const vorwahl = kunden.find(k => k.kundennummer && k.kundennummer.toUpperCase() === nr) || (z.freigabe && kunden.find(k => k.firma === z.freigabe.firma)) || null;
    const kunde = h('select', {}, [h('option', { value: '' }, '– Kunde wählen –')].concat(kunden.map(k => h('option', { value: k.id, 'data-domain': k.domain || '', selected: !!vorwahl && vorwahl.id === k.id }, k.kundennummer + ' · ' + k.firma))));
    const dom = h('input', { placeholder: 'Domain ohne www, z. B. elbdetail.de', maxlength: 253, autocomplete: 'off', value: vorwahl && vorwahl.domain ? String(vorwahl.domain).replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/\/.*$/, '') : '' });
    kunde.addEventListener('change', () => { const x = (kunde.selectedOptions[0].getAttribute('data-domain') || '').replace(/^https?:\/\//, '').replace(/^www\./, '').replace(/\/.*$/, ''); if (x && !dom.value) dom.value = x; });
    const st = z.freigabe ? { wartet: 'Der Kunde hat die Vorschau noch nicht freigegeben.', freigegeben: 'Der Kunde hat die Vorschau freigegeben.', abgelehnt: 'Der Kunde hat die Vorschau abgelehnt.', zurueckgezogen: 'Die Freigabe-Anfrage wurde zurückgezogen.' }[z.freigabe.status] : 'Zu dieser Demo gibt es keine Freigabe-Anfrage.';
    const los = h('button', { class: 'btn', type: 'button' }, 'Jetzt live schalten');
    const senden = async (trotzdem) => api('/api/admin/websites/demo-zu-live', { method: 'POST', body: { demo: z.name, domain: dom.value, kunden_id: kunde.value, trotzdem } });
    const d = dialog('Demo „' + z.name + '“ live schalten', h('div', {}, h('p', { class: 'small' }, st), h('p', { class: 'small muted' }, 'Die Demo wird so, wie sie ist, auf die Kundendomain gelegt. Eine bestehende Live-Seite wird dabei ersetzt, die vorige Version bleibt gesichert.'),
      h('label', {}, 'Domain der Kunden-Website'), dom, h('label', {}, 'Kunde'), kunde, dm, h('p', {}, los)));
    los.addEventListener('click', async () => {
      melde(dm, ''); los.disabled = true;
      try {
        let r;
        try { r = await senden(false); }
        catch (x) { if (/trotzdem live schalten/.test(x.message) && confirm(x.message)) r = await senden(true); else throw x; }
        d.zu(); melde(m, r.hinweis, 'ok'); if (r.check) checkZeigen(r.check, dom.value); setTimeout(() => location.reload(), 4000);
      } catch (x) { melde(dm, x.message); los.disabled = false; }
    });
  } }, 'Live schalten');
  const zurueck = (z) => h('button', { class: 'btn small sec', onclick: async () => {
    try { const r = await api('/api/admin/websites/wiederherstellen', { method: 'POST', body: { id: z.id } }); melde(m, r.hinweis, 'ok'); setTimeout(() => location.reload(), 1500); }
    catch (x) { melde(m, x.message); }
  } }, 'Wiederherstellen');
  const korbWeg = (z) => h('button', { class: 'btn small bad', onclick: async () => {
    if (!confirm('„' + z.name + '“ endgültig löschen? Das kann nicht rückgängig gemacht werden.')) return;
    try { const r = await api('/api/admin/websites/papierkorb-loeschen', { method: 'POST', body: { id: z.id } }); melde(m, r.hinweis, 'ok'); setTimeout(() => location.reload(), 1500); }
    catch (x) { melde(m, x.message); }
  } }, 'Endgültig löschen');
  const korbLeeren = () => h('button', { class: 'btn small bad', onclick: async () => {
    if (!confirm('Den ganzen Papierkorb endgültig leeren? Das kann nicht rückgängig gemacht werden.')) return;
    try { const r = await api('/api/admin/websites/papierkorb-loeschen', { method: 'POST', body: { alle: true } }); melde(m, r.hinweis, 'ok'); setTimeout(() => location.reload(), 1500); }
    catch (x) { melde(m, x.message); }
  } }, 'Papierkorb leeren');
  const checkKnopf = (z) => h('button', { class: 'btn small sec', onclick: async () => { try { checkZeigen(await api('/api/admin/websites/livecheck?art=' + z.art + '&name=' + encodeURIComponent(z.name)), z.name); } catch (x) { melde(m, x.message); } } }, 'Check');
  const dnsKnopf = (z) => z.art !== 'live' ? '' : h('span', {}, z.dns ? h('span', { class: 'pill ' + (z.dns.ok ? 'ok' : 'warn') }, z.dns.ok ? 'DNS ok' : 'DNS offen') : '', ' ',
    h('button', { class: 'btn small sec', onclick: async () => { try { dnsZeigen(await api('/api/admin/websites/domain/' + encodeURIComponent(z.name))); } catch (x) { melde(m, x.message); } } }, 'DNS prüfen'), ' ',
    h('button', { class: 'btn small', title: 'DNS, Startseite, Website-API und Zertifikat sofort neu prüfen', onclick: async (ev) => {
      ev.target.disabled = true; ev.target.textContent = 'Prüfe …';
      try { const r = await api('/api/admin/websites/jetzt-pruefen', { method: 'POST', body: { domain: z.name } }); melde(m, z.name + ': ' + r.text, r.zustand === 'ok' ? 'ok' : ''); if (r.zustand === 'dns') dnsZeigen(r.dns); setTimeout(() => location.reload(), r.zustand === 'dns' ? 6000 : 2500); }
      catch (x) { melde(m, x.message); ev.target.disabled = false; ev.target.textContent = 'Jetzt prüfen'; }
    } }, 'Jetzt prüfen'));
  const status = (z) => {
    if (z.art === 'live') {
      const w = z.wacht;
      if (!w) return h('span', { class: 'muted small' }, 'noch nicht geprüft');
      if (!w.ok && w.wartet_dns) return h('span', {}, h('span', { class: 'pill warn', title: 'Neue Seite: die Domain zeigt noch nicht auf den Server. Das ist kein Ausfall. ' + (w.fehler || '') }, 'wartet auf DNS'), ' ', h('span', { class: 'small muted' }, 'kein Alarm'));
      return h('span', {}, h('span', { class: 'pill ' + (w.ok ? 'ok' : 'bad'), title: w.fehler || '' }, w.ok ? 'erreichbar' : 'gestört'), ' ',
        h('span', { class: 'small muted' }, (w.ms ? w.ms + ' ms · ' : '') + (w.prozent != null ? String(w.prozent).replace('.', ',') + ' % · ' : '') + (w.cert_tage != null ? 'Zertifikat ' + w.cert_tage + ' T' : '') + (w.qualitaet ? ' · ' + (w.qualitaet.tote.length ? w.qualitaet.tote.length + ' tote Links' : 'Links ok') + (w.qualitaet.langsam.length ? ' · ' + w.qualitaet.langsam.length + ' langsam' : '') : '')));
    }
    const f = z.freigabe;
    if (!f) return '';
    const t = { wartet: ['warn', 'Freigabe wartet'], freigegeben: ['ok', 'vom Kunden freigegeben'], abgelehnt: ['bad', 'Änderung gewünscht'], zurueckgezogen: ['', 'zurückgezogen'] }[f.status] || ['', f.status];
    return h('span', {}, h('span', { class: 'pill ' + t[0], title: f.kommentar || '' }, t[1]), f.entschieden_am ? h('span', { class: 'small muted' }, ' ' + new Date(f.entschieden_am).toLocaleString('de-DE', { dateStyle: 'short', timeStyle: 'short' }) + (f.entschieden_name ? ' · ' + f.entschieden_name : '')) : '');
  };
  return h('div', { class: 'stack' }, kopf('Websites & Demos'), m, dnsBox, await statusKarte(), await uploadKarte(d), await vorschauKarte(d), await sicherungKarte(d),
    h('div', { class: 'card' }, h('h2', {}, 'Aktiv'),
      tabelle([['Art', z => z.art === 'live' ? 'Live' : 'Demo'], ['Name', z => z.name], ['Kunde', z => z.kunde], ['Status', status], ['DNS', dnsKnopf], ['Größe', z => mb(z.groesse)], ['Dateien', z => z.dateien], ['Zuletzt geändert', z => z.geaendert ? wann(z.geaendert) : ''], ['', z => h('span', {}, checkKnopf(z), ' ', liveKnopf(z), ' ', loesch(z))]], d.aktiv, 'Noch keine Seiten angelegt (mkctl site-add / demo-add).')),
    h('div', { class: 'card' }, h('h2', {}, 'Papierkorb'), h('p', { class: 'small muted' }, 'Gelöschte Seiten bleiben ' + d.aufbewahrung_tage + ' Tage erhalten und werden dann endgültig entfernt.'),
      tabelle([['Art', z => z.art === 'live' ? 'Live' : 'Demo'], ['Name', z => z.name], ['Gelöscht', z => wann(z.geloescht)], ['Größe', z => mb(z.groesse)], ['', z => h('span', {}, zurueck(z), ' ', korbWeg(z))]], d.papierkorb, 'Papierkorb ist leer.'), d.papierkorb.length ? h('p', {}, korbLeeren()) : ''));
};


// ---------------------------------------------------------------- Preise und Konditionen
async function preisaenderungKarte() {
  const m = h('div'), box = h('div'), liste = h('div');
  const euroC = (c) => fmtEuro(c);
  const frist = new Date(Date.now() + 45 * 86400000).toISOString().slice(0, 10);
  const laden = async () => {
    const d = await api('/api/admin/preisaenderungen');
    liste.replaceChildren(tabelle([['Titel', z => z.titel], ['Anpassung', z => String(z.prozent).replace('.', ',') + ' %'], ['Wirksam ab', z => datum(z.wirksam_ab)],
      ['Status', z => ({ entwurf: 'Entwurf', angekuendigt: 'angekündigt', angewendet: 'angewendet', abgebrochen: 'abgebrochen' })[z.status]], ['Kunden', z => z.kunden + ' (gelesen ' + z.gelesen + ', Einwand ' + z.widersprueche + ')'],
      ['', z => h('span', { class: 'row' }, knopf('Details', async () => {
          const r = await api('/api/admin/preisaenderungen/' + z.id);
          box.replaceChildren(h('div', { class: 'card' }, h('h3', {}, r.aenderung.titel), tabelle([['Kunde', k => k.firma], ['Alt', k => euroC(k.alt_cent)], ['Neu', k => euroC(k.neu_cent)], ['Benachrichtigt', k => k.benachrichtigt_am ? datum(k.benachrichtigt_am) : '–'], ['Gelesen', k => k.gelesen_am ? datum(k.gelesen_am) : '–'], ['Einwand', k => k.widerspruch_am ? (k.widerspruch_text || 'ja') : '–'], ['Angewendet', k => k.angewendet_am ? datum(k.angewendet_am) : '–']], r.kunden, '')));
        }, 'sec small'),
        ['entwurf', 'angekuendigt'].includes(z.status) ? knopf(z.status === 'entwurf' ? 'Jetzt ankündigen' : 'Fehlende nachsenden', async () => { if (!confirm('Die Ankündigung per Mail an alle betroffenen Kunden senden?')) return; try { const r = await api('/api/admin/preisaenderungen/' + z.id + '/ankuendigen', { method: 'POST', body: {} }); melde(m, r.gesendet + ' gesendet' + (r.fehlgeschlagen ? ', ' + r.fehlgeschlagen + ' nicht zustellbar (keine E-Mail-Adresse oder Fehler)' : '') + '.', 'ok'); laden(); } catch (x) { fehler(m, x); } }, 'small') : '',
        ['entwurf', 'angekuendigt'].includes(z.status) ? knopf('Abbrechen', async () => { if (!confirm('Preisänderung abbrechen? Bereits versendete Ankündigungen musst du den Kunden selbst widerrufen.')) return; try { await api('/api/admin/preisaenderungen/' + z.id + '/abbrechen', { method: 'POST', body: {} }); laden(); } catch (x) { fehler(m, x); } }, 'bad small') : '')]], d.liste, 'Noch keine Preisanpassung.'));
  };
  const f = h('form', { onsubmit: async (e) => { e.preventDefault(); const o = formular(e.target); const body = { titel: o.titel, prozent: Number(String(o.prozent).replace(',', '.')), wirksam_ab: o.wirksam_ab, text: o.text };
    try { const v = await api('/api/admin/preisaenderungen/vorschau', { method: 'POST', body });
      box.replaceChildren(h('div', { class: 'card' }, h('h3', {}, 'Vorschau: ' + v.kunden.length + ' Kunden'), tabelle([['Kunde', k => k.firma], ['Monatlich alt', k => euroC(k.alt_cent)], ['Monatlich neu', k => euroC(k.neu_cent)]], v.kunden, ''),
        h('p', {}, 'Summe monatlich: ' + euroC(v.summe_alt_cent) + ' → ' + euroC(v.summe_neu_cent)),
        h('p', {}, knopf('Als Entwurf anlegen', async () => { try { await api('/api/admin/preisaenderungen', { method: 'POST', body }); box.replaceChildren(); melde(m, 'Entwurf angelegt. Jetzt in der Liste „Jetzt ankündigen“.', 'ok'); laden(); } catch (x) { fehler(m, x); } }, 'btn'))));
    } catch (x) { fehler(m, x); } } },
    h('div', { class: 'form2' }, feld('Titel', 'titel', 'Preisanpassung ' + new Date().getFullYear(), { required: true, minlength: 3 }), feld('Anpassung in %', 'prozent', '', { required: true, type: 'text', placeholder: 'z. B. 5' }), feld('Wirksam ab (mind. 30 Tage Frist)', 'wirksam_ab', frist, { type: 'date', required: true }), feld('Text für die Kunden (optional)', 'text', '')),
    h('p', {}, h('button', { class: 'btn' }, 'Vorschau berechnen')));
  await laden();
  return h('div', { class: 'card' }, h('h2', {}, 'Preiserhöhung ankündigen'),
    h('p', { class: 'small muted' }, 'Erhöht die monatlichen Preise aller aktiven Kunden (ohne Referenzkunden und ohne laufende Kündigung) um einen Prozentsatz. Jeder Kunde bekommt eine Mail mit altem und neuem Preis und kann bestätigen oder Einwände senden. Kunden mit Einwand bleiben beim alten Preis. Zum Stichtag werden die Preise automatisch angepasst, auch feste Positionen in Wartungsplänen. Ob und wie du einseitig erhöhen darfst, regelt dein Vertrag: bitte vorher prüfen.'), m, f, box, liste);
}

V.preise = async () => {
  const d = await api('/api/admin/preise'), m = h('div'), mk = h('div'), mr = h('div');
  const heute = new Date().toISOString().slice(0, 10);
  const pform = h('form', { onsubmit: (e) => { e.preventDefault(); const o = formular(e.target);
    const body = { produkt_code: o.produkt_code, gueltig_ab: o.gueltig_ab, einrichtung_cent: cent(o.einrichtung), monatlich_cent: cent(o.monatlich), projekt_cent: cent(o.projekt), ab_preis: !!e.target.ab.checked };
    bestaetigt(m, () => api('/api/admin/preise', { method: 'POST', body }), 'Neuer Preis gespeichert. Bestehende Buchungen behalten ihren Preis.'); } },
    h('div', { class: 'form2' }, h('div', {}, h('label', {}, 'Produkt'), h('select', { name: 'produkt_code' }, d.aktuell.map(p => h('option', { value: p.code }, p.name + ' (' + p.code + ')')))),
      feld('Gültig ab', 'gueltig_ab', heute, { type: 'date', required: true }), feld('Einrichtung in €', 'einrichtung', '', { type: 'number', step: '0.01', min: '0' }), feld('Monatlich in €', 'monatlich', '', { type: 'number', step: '0.01', min: '0' }), feld('Projekt in €', 'projekt', '', { type: 'number', step: '0.01', min: '0' })),
    h('label', { style: 'display:flex;gap:8px;align-items:center;color:inherit;font-size:14px' }, h('input', { type: 'checkbox', name: 'ab', style: 'width:auto' }), '„ab"-Preis'),
    h('p', {}, h('button', { class: 'btn' }, 'Neuen Preis anlegen')));
  const kond = (z) => { const i = h('input', { value: z.wert_zahl ?? z.wert_text ?? '' }); return h('div', { class: 'row' }, h('div', { class: 'grow' }, i),
    knopf('Speichern', () => { const v = i.value.trim(); const body = /^-?\d+$/.test(v) ? { wert_zahl: Number(v) } : { wert_text: v }; bestaetigt(mk, () => api('/api/admin/konditionen/' + encodeURIComponent(z.schluessel), { method: 'PUT', body })); })); };
  const regelBtn = (z) => z.status === 'entwurf' ? knopf('Freigeben', () => confirm('Regel "' + z.name + '" (' + z.prozent + ' %) freigeben?') && bestaetigt(mr, () => api('/api/admin/provisionsregeln/' + z.id + '/freigeben', { method: 'POST' }), 'Freigegeben.')) : '';
  const lt = await leistungstextKarte().catch(() => '');
  return h('div', { class: 'stack' }, kopf('Preise & Konditionen'), m, await preisaenderungKarte(),
    h('div', { class: 'card' }, h('h2', {}, 'Aktuelle Preise'), tabelle([['Produkt', z => z.name], ['Einrichtung', z => (z.ab_preis ? 'ab ' : '') + fmtEuro(z.einrichtung_cent)], ['Monatlich', z => fmtEuro(z.monatlich_cent)], ['Projekt', z => fmtEuro(z.projekt_cent)], ['Gültig ab', z => datum(z.gueltig_ab)]], d.aktuell)),
    h('div', { class: 'card' }, h('h2', {}, 'Preis ändern (neue Version)'), h('p', { class: 'small muted' }, 'Alte Preise bleiben im Verlauf. Bestehende Buchungen behalten den Preis, der bei der Buchung galt.'), pform), lt,
    h('div', { class: 'card' }, h('h2', {}, 'Konditionen'), mk, tabelle([['Schlüssel', z => z.schluessel], ['Beschreibung', z => z.beschreibung], ['Wert', kond]], d.konditionen, 'Keine Konditionen.')),
    h('div', { class: 'card' }, h('h2', {}, 'Provisionsregeln'), h('p', { class: 'small muted' }, 'Entwürfe gelten erst nach deiner Freigabe.'), mr, tabelle([['Regel', z => z.name], ['Monate', z => z.von_monat + (z.bis_monat ? '–' + z.bis_monat : '+')], ['%', z => z.prozent], ['Status', z => pill(z.status === 'entwurf' ? 'onboarding' : z.status)], ['', regelBtn]], d.provisionsregeln)),
    h('div', { class: 'card' }, h('h2', {}, 'Preisverlauf'), tabelle([['Gültig ab', z => datum(z.gueltig_ab)], ['Produkt', z => z.produkt_code], ['Einrichtung', z => fmtEuro(z.einrichtung_cent)], ['Monatlich', z => fmtEuro(z.monatlich_cent)], ['Projekt', z => fmtEuro(z.projekt_cent)], ['Freigegeben von', z => z.freigegeben_von]], d.verlauf)));
};

// ---------------------------------------------------------------- Datenschutz und Qualität
V.compliance = async () => {
  const d = await api('/api/admin/compliance'), m = h('div');
  const tun = (fn) => bestaetigt(m, fn, 'Erledigt.');
  const post = (pfad, body) => api('/api/admin' + pfad, { method: 'POST', body });
  const entscheid = (tab, okTxt, okStatus, neinTxt, neinStatus) => (z) => h('span', { class: 'row' },
    knopf(okTxt, () => tun(() => post('/compliance/' + tab + '/' + z.id, { status: okStatus })), 'sec'),
    neinTxt && knopf(neinTxt, () => { const b = prompt('Begründung (kurz):'); if (b !== null) tun(() => post('/compliance/' + tab + '/' + z.id, { status: neinStatus, begruendung: b })); }, 'bad'));
  const sektion = (titel, zeilen, spalten, leer) => h('div', { class: 'card' }, h('h2', {}, titel + ' (' + zeilen.length + ')'), tabelle(spalten, zeilen, leer));
  const stufe = (s) => h('span', { class: 'pill ' + (s === 'kritisch' ? 'bad' : s === 'warnung' ? 'warn' : '') }, s);
  const offen = d.alarme.length + d.freigaben.length + d.aenderungen.length + d.auskunft.length + d.workflow_fehler.length + d.befunde.length + d.massnahmen.length;
  const vs = await api('/api/admin/vertragsstand').catch(() => null);
  const stand = vs ? h('div', { class: 'card' }, h('h2', {}, 'Stand der AVV-Zusagen ', h('span', { class: 'pill ' + ({ ok: 'ok', warn: 'warn', bad: 'bad' }[vs.gesamt] || '') }, vs.gesamt === 'ok' ? 'alles eingehalten' : vs.gesamt === 'bad' ? 'Handlungsbedarf' : vs.gesamt === 'warn' ? 'bitte prüfen' : 'teils unbekannt')),
    h('p', { class: 'small muted' }, 'Zeigt, ob das, was im Vertrag steht (Anlage 2), im Betrieb gerade stimmt. Als Nachweis bei Rückfragen von Kunden.'),
    tabelle([['', z => h('span', { class: 'pill ' + ({ ok: 'ok', warn: 'warn', bad: 'bad' }[z.status] || '') }, { ok: 'ok', warn: 'prüfen', bad: 'Problem', unbekannt: '?' }[z.status])], ['Punkt', z => z.titel], ['Stand', z => z.detail]], vs.punkte)) : '';
  return h('div', { class: 'stack' }, kopf('Datenschutz & Qualität', h('span', { class: 'pill ' + (offen ? 'warn' : 'ok') }, offen ? offen + ' offen' : 'alles erledigt')), stand, m,
    sektion('Alarme', d.alarme, [['Zeit', z => zeit(z.zeit)], ['Stufe', z => stufe(z.stufe)], ['Quelle', z => z.quelle], ['Titel', z => z.titel], ['', z => knopf('Bestätigen', () => tun(() => post('/alarme/' + z.id + '/bestaetigen')))]], 'Keine offenen Alarme.'),
    sektion('Freigaben (Agenten)', d.freigaben, [['Eingang', z => zeit(z.erstellt_am)], ['Kunde', z => z.kundennummer || ''], ['Art', z => z.art], ['Vorschau', z => z.vorschau], ['', entscheid('freigaben', 'Freigeben', 'freigegeben', 'Ablehnen', 'abgelehnt')]], 'Keine offenen Freigaben.'),
    sektion('Änderungsfreigaben', d.aenderungen, [['Seit', z => datum(z.beantragt_am)], ['Art', z => z.art], ['Gegenstand', z => z.gegenstand], ['Beschreibung', z => z.beschreibung], ['Von', z => z.beantragt_von], ['', entscheid('aenderungsfreigaben', 'Freigeben', 'freigegeben', 'Ablehnen', 'abgelehnt')]], 'Keine offenen Anträge.'),
    sektion('Auskunfts- und Löschanfragen (DSGVO)', d.auskunft, [['Eingang', z => datum(z.eingang_am)], ['Frist', z => datum(z.frist_bis)], ['Art', z => z.art], ['Person', z => z.person_ref], ['Status', z => pill(z.status)], ['', entscheid('auskunftsanfragen', 'Erledigt', 'erledigt', 'Ablehnen', 'abgelehnt')]], 'Keine offenen Anfragen.'),
    sektion('Workflow-Fehler', d.workflow_fehler, [['Zeit', z => zeit(z.zeit)], ['Workflow', z => z.workflow_name], ['Knoten', z => z.knoten], ['Fehler', z => z.fehlertext], ['', z => knopf('Behoben', () => tun(() => post('/workflow-fehler/' + z.id + '/behoben')))]], 'Keine offenen Fehler.'),
    sektion('Befunde (Qualität)', d.befunde, [['Gefunden', z => datum(z.gefunden_am)], ['Schwere', z => stufe(z.schwere === 'kritisch' ? 'kritisch' : z.schwere === 'wesentlich' ? 'warnung' : 'info')], ['Titel', z => z.titel], ['Status', z => pill(z.status)], ['', entscheid('befunde', 'Behoben', 'behoben', '', '')]], 'Keine offenen Befunde.'),
    sektion('Maßnahmen', d.massnahmen, [['Fällig', z => datum(z.faellig_am)], ['Maßnahme', z => z.beschreibung], ['Verantwortlich', z => z.verantwortlich], ['Status', z => pill(z.status)], ['', entscheid('massnahmen', 'Umgesetzt', 'umgesetzt', '', '')]], 'Keine offenen Maßnahmen.'));
};

/** Nutzungsmessung: welche Seiten werden gebraucht, wer ist aktiv. Nur Seitennamen und Zähler, keine Inhalte. */
const ALLE_SEITEN = { kunde: 'heute uebersicht status briefing nachrichten freigaben assistent anfragen termine bewertungen kontakte dokumente unterlagen auswertung berichte belege anrufe website wochenangebote werbung automationen avv team hilfe einstellungen'.split(' '),
  vertrieb: 'heute uebersicht leads pipeline angebote leitfaden kunden provisionen konto'.split(' ') };
const ROLLE = { kunde: 'Kunden', vertrieb: 'Vertriebler', admin: 'Admin' };
async function nutzungsKarte() {
  const d = await api('/api/admin/nutzung?tage=30');
  const tageGemessen = d.messung_seit ? Math.floor((Date.now() - new Date(d.messung_seit).getTime()) / 864e5) : 0, genug = tageGemessen >= 14;
  const block = (rolle) => {
    const z = d.seiten.filter(x => x.rolle === rolle), max = Math.max(1, ...z.map(x => x.aufrufe)), selten = z.filter(x => x.aufrufe < 3), nie = (ALLE_SEITEN[rolle] || []).filter(sid => !z.some(x => x.seite === sid));
    return h('div', { style: 'margin:10px 0' }, h('h3', {}, ROLLE[rolle] + ': ' + (d.aktiv[rolle] || 0) + ' von ' + (d.konten[rolle] || 0) + ' Konten aktiv (7 Tage: ' + (d.aktiv_7_tage[rolle] || 0) + ')'),
      z.length ? h('div', { class: 'dtrichter' }, z.slice(0, 8).map(x => h('div', { class: 'tstufe' }, h('span', { class: 'tname' }, x.seite), h('div', { class: 'tbalken' }, h('div', { style: 'height:100%;border-radius:10px;background:var(--grad);width:' + Math.max(3, Math.round(x.aufrufe / max * 100)) + '%' })), h('span', { class: 'tzahl' }, x.aufrufe)))) : h('p', { class: 'small muted' }, 'Noch keine Aufrufe.'),
      !genug ? '' : [nie.length ? h('p', { class: 'small' }, h('b', {}, 'Nie geöffnet (30 Tage): '), nie.join(', '), h('span', { class: 'muted' }, ' – Kandidaten zum Ausblenden oder Entfernen.')) : '',
        selten.length ? h('p', { class: 'small muted' }, 'Selten (unter 3 Aufrufe): ' + selten.map(x => x.seite).join(', ')) : ''] );
  };
  return h('div', { class: 'card' }, h('h2', {}, 'Nutzung (30 Tage)'),
    h('p', { class: 'small muted' }, 'Gezählt werden nur Seitenname, Tag und Rolle, dazu wer an einem Tag aktiv war. Keine Inhalte, nach 180 Tagen gelöscht. ' + (d.messung_seit ? 'Messung seit ' + datum(d.messung_seit) + '.' : 'Die Messung beginnt mit dem ersten Aufruf.')),
    genug ? '' : h('p', { class: 'msg info' }, 'Die Messung läuft erst seit ' + tageGemessen + ' Tagen. Aussagen zu ungenutzten Seiten gibt es ab 14 Tagen, vorher wäre das Zufall.'),
    d.tour.alle ? h('p', { class: 'small' }, 'Erststart-Tour gesehen: ' + d.tour.gesehen + ' von ' + d.tour.alle + ' Kundenkonten.') : '',
    ['kunde', 'vertrieb', 'admin'].map(block));
}

V.protokoll = async () => {
  const d = await api('/api/admin/audit');
  return h('div', {}, kopf('Protokoll'), await nutzungsKarte().catch(() => ''), h('div', { class: 'card' }, tabelle([['Zeit', z => zeit(z.zeit)], ['Benutzer', z => z.email || 'System'], ['Kunde', z => z.kundennummer || ''], ['Aktion', z => z.aktion], ['Details', z => JSON.stringify(z.details)]], d)));
};

