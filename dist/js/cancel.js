// Kund:innen-Storno über den Link aus der Bestätigungs-Mail
const box = document.querySelector('[data-cancel]');
const btn = box.querySelector('[data-cancel-btn]');
btn?.addEventListener('click', async () => {
  btn.disabled = true;
  const msg = box.querySelector('[data-cancel-msg]');
  const res = await fetch('/api/cancel.php', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ id: box.dataset.id, t: box.dataset.token }) });
  const data = await res.json().catch(() => ({}));
  if (res.ok) { msg.textContent = 'Ihr Termin wurde storniert.' + (data.refunded ? ' Die Erstattung ist veranlasst.' : ''); btn.remove(); }
  else { msg.textContent = data.error || 'Stornierung fehlgeschlagen.'; btn.disabled = false; }
});
