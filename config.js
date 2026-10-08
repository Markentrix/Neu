// Einstellungen der Website. Hier trägt der Betrieb bzw. der Webentwickler die Werte ein.
window.SITE_CONFIG = {
  // E-Mail-Adresse der Fleischerei (Fallback und Anzeige bei Fehlern)
  orderEmail: "bestellung@example.de",

  // Adresse des Bestell-Backends (JSON-POST). Leer lassen = Bestellung wird als Text
  // zum Kopieren bzw. per E-Mail angezeigt. Beispiel für später:
  // "https://<projekt>.supabase.co/functions/v1/order"
  orderEndpoint: ""
};
