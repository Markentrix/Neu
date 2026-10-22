<?php /* Buchungs-Widget – eingebunden über booking_widget() in partials.php */ ?>
<div class="booking" data-booking>
  <ol class="steps" aria-label="Buchungsschritte">
    <li class="is-active" data-step-label="1"><span>1</span> Leistung</li>
    <li data-step-label="2"><span>2</span> Termin</li>
    <li data-step-label="3"><span>3</span> Daten</li>
    <li data-step-label="4"><span>4</span> Zahlung</li>
  </ol>

  <div class="booking-body">
    <div class="booking-main">
      <section class="step" data-step="1" aria-labelledby="st1">
        <h3 id="st1" class="step-title">Welche Leistungen wünschen Sie?</h3>
        <p class="hint">Mehrfachauswahl möglich, z. B. Färben + Schnitt (max. <?= (int)$c['booking']['maxServices'] ?>).</p>
        <div class="service-picker" data-service-picker>
          <?php foreach ($c['categories'] as $i => $cat): ?>
          <details class="service-cat"<?= $i === 0 ? ' open' : '' ?>>
            <summary><span><?= e($cat['title']) ?></span><span class="count" hidden></span></summary>
            <div class="service-options">
              <?php foreach ($cat['services'] as $sv): $full = services()[$sv['id']]; ?>
              <label class="service-option"><input type="checkbox" value="<?= e($sv['id']) ?>"><span><span class="n"><?= e($full['fullName']) ?></span><small>ca. <?= e(duration_label((int)$sv['duration'])) ?></small></span><span class="price"><?= e(price_label($full)) ?></span></label>
              <?php endforeach; ?>
            </div>
          </details>
          <?php endforeach; ?>
        </div>
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
        <div class="slots" data-slots aria-live="polite"></div>
        <div class="step-actions">
          <button class="btn btn-ghost" type="button" data-back>Zurück</button>
          <button class="btn btn-gold" type="button" data-next disabled>Weiter</button>
        </div>
      </section>

      <section class="step" data-step="3" hidden aria-labelledby="st3">
        <h3 id="st3" class="step-title">Ihre Kontaktdaten</h3>
        <form class="form-grid" data-customer-form novalidate>
          <label>Vor- und Nachname*<input name="name" autocomplete="name" required minlength="2" maxlength="80"></label>
          <label>Telefon*<input name="phone" type="tel" autocomplete="tel" required maxlength="25"></label>
          <label class="full">E-Mail* <small>(für die Bestätigung)</small><input name="email" type="email" autocomplete="email" required maxlength="254"></label>
          <label class="full">Anmerkung <small>(optional, z. B. Haarlänge, Wunschfarbe)</small><textarea name="note" rows="3" maxlength="500"></textarea></label>
          <label class="hp" aria-hidden="true">Website<input name="website" tabindex="-1" autocomplete="off"></label>
          <label class="check full"><input type="checkbox" name="followupOptin"> <span>Optional: Erinnert mich einmalig per E-Mail, wenn mein nächster Termin fällig ist (z. B. Ansatz oder Nachschnitt).</span></label>
          <?php if (!empty($s['reviewUrl'])): ?>
          <label class="check full"><input type="checkbox" name="reviewOptin"> <span>Optional: Nach dem Termin dürft ihr mich einmalig per E-Mail um eine Google-Bewertung bitten.</span></label>
          <?php endif; ?>
          <label class="check full"><input type="checkbox" name="consent" required> <span>Ich bin einverstanden, dass meine Angaben zur Terminvereinbarung verarbeitet werden. Details in der <a href="/datenschutz" target="_blank" rel="noopener">Datenschutzerklärung</a>.*</span></label>
          <p class="form-error full" data-form-error role="alert" hidden></p>
        </form>
        <div class="step-actions">
          <button class="btn btn-ghost" type="button" data-back>Zurück</button>
          <button class="btn btn-gold" type="button" data-next>Weiter zur Zahlung</button>
        </div>
      </section>

      <section class="step" data-step="4" hidden aria-labelledby="st4">
        <h3 id="st4" class="step-title">Wie möchten Sie bezahlen?</h3>
        <div class="pay-options">
          <label class="pay-option" data-paypal-option hidden>
            <input type="radio" name="payment" value="paypal">
            <span><strong>Jetzt mit PayPal bezahlen</strong><small data-paypal-label></small></span>
          </label>
          <label class="pay-option">
            <input type="radio" name="payment" value="onsite" checked>
            <span><strong>Vor Ort bezahlen</strong><small>Bar oder Karte im Salon</small></span>
          </label>
        </div>
        <div class="paypal-box" data-paypal-box hidden>
          <div data-paypal-buttons></div>
          <p class="hint">Ihr Termin ist erst nach erfolgreicher Zahlung gebucht. Mit dem Laden von PayPal werden Daten an PayPal (Europe) übermittelt.</p>
        </div>
        <p class="form-error" data-pay-error role="alert" hidden></p>
        <div class="step-actions">
          <button class="btn btn-ghost" type="button" data-back>Zurück</button>
          <button class="btn btn-gold" type="button" data-submit-onsite>Verbindlich buchen</button>
        </div>
      </section>

      <section class="step confirmation" data-step="done" hidden tabindex="-1" aria-labelledby="st5">
        <div class="check-circle" aria-hidden="true"><svg viewBox="0 0 52 52"><path class="check-path" pathLength="1" d="M15 27l7.5 7.5L38 19" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/></svg><span class="spark s1"></span><span class="spark s2"></span><span class="spark s3"></span><span class="spark s4"></span><span class="spark s5"></span><span class="spark s6"></span></div>
        <h3 id="st5" class="step-title">Vielen Dank – Ihr Termin ist gebucht!</h3>
        <p data-confirmation-text></p>
        <p class="hint">Eine Bestätigung ist unterwegs in Ihr Postfach. Bis <?= (int)$c['booking']['freeCancelHours'] ?> Stunden vorher können Sie dort kostenfrei stornieren.</p>
        <div class="step-actions center">
          <a class="btn btn-ghost" href="#" data-ics download="aj-atelier-termin.ics">In Kalender eintragen</a>
          <button class="btn btn-gold" type="button" data-restart>Weiteren Termin buchen</button>
        </div>
      </section>
    </div>

    <div class="booking-summary">
      <h3>Ihre Auswahl</h3>
      <ul data-summary-list><li class="muted">Noch keine Leistung gewählt</li></ul>
      <dl>
        <div><dt>Dauer</dt><dd data-summary-duration>–</dd></div>
        <div><dt>Termin</dt><dd data-summary-date>–</dd></div>
        <div><dt>Preis</dt><dd data-summary-price>–</dd></div>
      </dl>
      <p class="hint" data-summary-hint hidden>Finaler Preis nach Aufwand – Kostenvoranschlag vor Ort.</p>
    </div>
  </div>
  <noscript><p class="form-error">Für die Online-Buchung wird JavaScript benötigt. Rufen Sie uns gerne an: <a href="tel:<?= $tel ?>"><?= e($s['phoneDisplay']) ?></a>.</p></noscript>
</div>
