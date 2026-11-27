/** Bild (Datei, Screenshot aus der Zwischenablage) für die KI vorbereiten: auf höchstens 1800 Pixel verkleinern und als JPEG (Base64 ohne Präfix) zurückgeben. */
export async function bildVorbereiten(datei) {
  const bmp = await createImageBitmap(datei);
  const f = Math.min(1, 1800 / Math.max(bmp.width, bmp.height)), c = document.createElement('canvas');
  c.width = Math.round(bmp.width * f); c.height = Math.round(bmp.height * f);
  const x = /** @type {CanvasRenderingContext2D} */ (c.getContext('2d'));
  x.fillStyle = '#fff'; x.fillRect(0, 0, c.width, c.height); x.drawImage(bmp, 0, 0, c.width, c.height);
  return c.toDataURL('image/jpeg', 0.9).split(',')[1];
}
