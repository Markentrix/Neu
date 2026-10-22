<?php /* Buchungsformular (Variante B des Website-Vertrags) – eingebunden über booking_widget() in partials.php.
   Leistungen, Mitarbeiter, freie Tage und Uhrzeiten kommen live aus dem Portal (/api/…), nichts davon ist hier fest eingetragen. */ ?>
<div class="booking" data-booking>
  <ol class="steps" aria-label="Buchungsschritte">
    <li class="is-active" data-step-label="1"><span>1</span> Leistung</li>
    <li data-step-label="2"><span>2</span> Termin</li>
    <li data-step-label="3"><span>3</span> Ihre Daten</li>
  </ol>

  <?= fallback_contact('Die Online-Buchung ist gerade nicht erreichbar. Rufen Sie uns gerne an, wir finden telefonisch einen Termin für Sie.') ?>

  <div class="booking-body" data-booking-body>
    <div class="booking-main">
      <section class="step" data-step="1" aria-labelledby="st1">
        <h3 id="st1" class="step-title">Welche Leistung wünschen Sie?</h3>
        <p class="hint">Weitere Wünsche, etwa Schnitt zusätzlich zur Farbe, können Sie im letzten Schritt angeben.</p>
        <div class="service-picker" data-service-picker aria-live="polite">
          <div class="loader" role="status" aria-label="Lade Leistungen"></div>
        </div>
        <label class="staff-pick" data-staff-wrap hidden>Wunschperson
          <select name="mitarbeiter" data-staff></select>
        </label>
        <div class="step-actions">
          <button class="btn btn-gold" type="button" data-next disabled>Weiter zur Terminwahl</button>
        </div>
      </section>

      <section class="step" data-step="2" hidden aria-labelledby="st2">
        <h3 id="st2" class="step-title">Wann passt es Ihnen?</h3>
        <div class="date-strip-wrap">
          <button class="icon-btn" type="button" data-date-prev aria-label="Frühere Tage">‹</button>
          <div class="date-strip" data-date-strip></div>
          <button class="icon-btn" type="button" data-date-next aria-label="Spätere Tage">›</button>
        </div>
        <p class="form-error" data-slot-error role="alert" hidden></p>
        <div class="slots" data-slots aria-live="polite"></div>
        <div class="step-actions">
          <button class="btn btn-ghost" type="button" data-back>Zurück</button>
          <button class="btn btn-gold" type="button" data-next disabled>Weiter</button>
        </div>
      </section>

      <section class="step" data-step="3" hidden aria-labelledby="st3">
        <h3 id="st3" class="step-title">Ihre Kontaktdaten</h3>
        <form class="form-grid" method="post" data-customer-form novalidate>
          <label>Vor- und Nachname*<input name="name" autocomplete="name" required minlength="2" maxlength="80"><small class="field-error" data-error-for="name"></small></label>
          <label>Telefon*<input name="telefon" type="tel" autocomplete="tel" required minlength="6" maxlength="30"><small class="field-error" data-error-for="telefon"></small></label>
          <label class="full">E-Mail* <small>(für die Bestätigung)</small><input name="email" type="email" autocomplete="email" required maxlength="254"><small class="field-error" data-error-for="email"></small></label>
          <label class="full" data-wish-wrap hidden>Gewünschte Leistung*<input name="wunsch" maxlength="120" placeholder="z. B. Balayage, Herrenschnitt"><small class="field-error" data-error-for="wunsch"></small></label>
          <label class="full">Anmerkung <small>(optional, z. B. Haarlänge, Wunschfarbe, weitere Leistungen)</small><textarea name="nachricht" rows="3" maxlength="1000"></textarea></label>
          <?= form_consent('zur Terminvereinbarung') ?>
          <small class="field-error full" data-error-for="einwilligung"></small>
          <p class="form-error full" data-form-error role="alert" hidden></p>
        </form>
        <div class="step-actions">
          <button class="btn btn-ghost" type="button" data-back>Zurück</button>
          <button class="btn btn-gold" type="button" data-submit>Termin verbindlich buchen</button>
        </div>
        <p class="hint">Bezahlt wird nach dem Termin im Salon, bar oder mit Karte.</p>
      </section>
    </div>

    <div class="booking-summary">
      <h3>Ihre Auswahl</h3>
      <dl>
        <div><dt>Leistung</dt><dd data-summary-service>–</dd></div>
        <div data-summary-staff-row hidden><dt>Bei</dt><dd data-summary-staff>–</dd></div>
        <div><dt>Dauer</dt><dd data-summary-duration>–</dd></div>
        <div><dt>Termin</dt><dd data-summary-date>–</dd></div>
        <div><dt>Preis</dt><dd data-summary-price>–</dd></div>
      </dl>
      <p class="hint" data-summary-hint hidden>Der Endpreis richtet sich nach Aufwand, vorab gibt es einen Kostenvoranschlag.</p>
    </div>
  </div>
</div>
