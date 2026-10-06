'use strict';
const PDFDocument = require('pdfkit');
const cfg = require('./config'); const { eur, fdate, round2, vatOf } = require('./money');
const addrLines = (a) => [`${a.first || ''} ${a.last || ''}`.trim(), a.company, a.street, `${a.zip || ''} ${a.city || ''}`.trim(), a.country === 'AT' ? 'Österreich' : 'Deutschland'].filter(Boolean);
function build(order, bank) {
  const doc = new PDFDocument({ size: 'A4', margin: 50, info: { Title: `Rechnung ${order.invoice_no || order.number}`, Author: cfg.company.name } });
  const chunks = []; doc.on('data', c => chunks.push(c));
  const done = new Promise(r => doc.on('end', () => r(Buffer.concat(chunks))));
  const items = JSON.parse(order.items), bill = JSON.parse(order.billing);
  doc.rect(0, 0, 595, 8).fill('#008C45'); doc.rect(198, 0, 199, 8).fill('#F4F5F0'); doc.rect(397, 0, 198, 8).fill('#CD212A');
  doc.fillColor('#06301B').font('Helvetica-Bold').fontSize(20).text(cfg.company.name, 50, 40);
  doc.font('Helvetica').fontSize(9).fillColor('#44564C').text(`${cfg.company.owner} · ${cfg.company.street} · ${cfg.company.zip} ${cfg.company.city}`, 50, 66);
  doc.fillColor('#14241B').fontSize(9).text(`${cfg.company.owner} – ${cfg.company.street} – ${cfg.company.zip} ${cfg.company.city}`, 50, 120, { underline: false });
  doc.fontSize(11).text(addrLines(bill).join('\n'), 50, 138);
  doc.font('Helvetica-Bold').fontSize(18).text(order.invoice_no ? 'Rechnung' : 'Bestellbestätigung', 50, 230);
  doc.font('Helvetica').fontSize(10);
  const meta = [['Rechnungsnr.', order.invoice_no || '–'], ['Rechnungsdatum', fdate(order.invoice_date || order.created_at)], ['Bestellnr.', order.number], ['Bestelldatum', fdate(order.created_at)], ['Kunden-E-Mail', order.email]];
  let y = 124; meta.forEach(([k, v]) => { doc.fillColor('#44564C').text(k, 360, y, { width: 90 }); doc.fillColor('#14241B').text(v, 452, y, { width: 100 }); y += 15; });
  y = 270; doc.rect(50, y, 495, 20).fill('#F0F9F4'); doc.fillColor('#06301B').font('Helvetica-Bold').fontSize(9);
  doc.text('Pos.', 56, y + 6); doc.text('Bezeichnung', 90, y + 6); doc.text('Menge', 350, y + 6, { width: 40, align: 'right' }); doc.text('Einzelpreis', 395, y + 6, { width: 70, align: 'right' }); doc.text('Gesamt', 470, y + 6, { width: 70, align: 'right' });
  y += 26; doc.font('Helvetica').fillColor('#14241B').fontSize(9);
  items.forEach((it, i) => {
    const h = doc.heightOfString(it.name, { width: 250 }); if (y + h > 740) { doc.addPage(); y = 60; }
    doc.text(String(i + 1), 56, y); doc.text(it.name, 90, y, { width: 250 }); doc.text(String(it.qty), 350, y, { width: 40, align: 'right' }); doc.text(eur(it.price), 395, y, { width: 70, align: 'right' }); doc.text(eur(round2(it.price * it.qty)), 470, y, { width: 70, align: 'right' });
    y += Math.max(h, 12) + 6; doc.moveTo(50, y - 3).lineTo(545, y - 3).strokeColor('#DCE6E0').lineWidth(.5).stroke();
  });
  y += 6; const row = (k, v, b) => { doc.font(b ? 'Helvetica-Bold' : 'Helvetica').fontSize(b ? 11 : 9).fillColor('#14241B').text(k, 330, y, { width: 130 }); doc.text(v, 460, y, { width: 80, align: 'right' }); y += b ? 20 : 14; };
  row('Zwischensumme', eur(order.subtotal)); if (order.discount) row(`Rabatt${order.coupon ? ' (' + order.coupon + ')' : ''}`, '−' + eur(order.discount)); row('Versand', order.shipping_cost ? eur(order.shipping_cost) : 'kostenlos'); row('Gesamtbetrag (brutto)', eur(order.total), true);
  doc.font('Helvetica').fontSize(8).fillColor('#44564C').text(`Im Gesamtbetrag sind ${(cfg.vatRate * 100).toFixed(0)} % Umsatzsteuer enthalten: ${eur(order.vat)} (Netto ${eur(round2(order.total - order.vat))}).`, 330, y, { width: 215 }); y += 34;
  const pay = { paypal: 'PayPal', card: 'Kreditkarte / Apple Pay / Google Pay', transfer: 'Überweisung (Vorkasse)', invoice: 'Rechnung' }[order.payment_method] || order.payment_method;
  doc.fontSize(9).fillColor('#14241B').font('Helvetica-Bold').text('Zahlung', 50, y); doc.font('Helvetica').text(`Zahlart: ${pay} · Status: ${order.payment_status}`, 50, y + 13); y += 30;
  if (['transfer', 'invoice'].includes(order.payment_method) && order.payment_status !== 'bezahlt' && bank && bank.iban) {
    doc.text(`Bitte überweisen Sie ${eur(order.total)} innerhalb von ${order.payment_method === 'invoice' ? '14' : '7'} Tagen unter Angabe „${order.number}“ an:\n${bank.holder} · ${bank.name} · IBAN ${bank.iban}${bank.bic ? ' · BIC ' + bank.bic : ''}`, 50, y, { width: 495 }); y += 40;
  }
  doc.fontSize(8).fillColor('#44564C').text('Leistungsdatum = Rechnungsdatum bzw. Lieferdatum. Versand versicherungsfrei innerhalb Deutschlands.', 50, y);
  doc.fontSize(8).fillColor('#44564C').text(`${cfg.company.name} · ${cfg.company.owner} · ${cfg.company.street} · ${cfg.company.zip} ${cfg.company.city} · Tel. ${cfg.company.phone} · ${cfg.company.email} · USt-IdNr. ${cfg.company.vat}`, 50, 790, { width: 495, align: 'center' });
  doc.end(); return done;
}
module.exports = { build };
