<?php
/**
 * Markentrix · gemeinsame Versandfunktionen (SMTP mit AUTH LOGIN, SSL oder STARTTLS, sonst mail()).
 * Wird von anfrage.php und wochenbericht.php eingebunden. Enthält nur Funktionen, keine Ausgabe.
 * Caddy reicht nur /api/anfrage.php und /api/check.php an PHP weiter, diese Datei ist von außen nicht ausführbar.
 *
 * $c erwartet die Schlüssel smtp_host, smtp_port, smtp_user, smtp_pass, smtp_security, from.
 */
declare(strict_types=1);

/** Minimaler SMTP-Versand (AUTH LOGIN, SSL auf 465 oder STARTTLS auf 587). Gibt true/false zurück. */
function smtp_send(array $c, string $to, string $subject, string $body, array $headers): bool {
  $sec  = $c['smtp_security'] ?: ($c['smtp_port'] === 465 ? 'ssl' : 'tls');
  $ssl  = $sec === 'ssl';
  $ctx  = stream_context_create(['ssl' => ['verify_peer' => true, 'verify_peer_name' => true, 'SNI_enabled' => true, 'peer_name' => $c['smtp_host']]]);
  $sock = @stream_socket_client(($ssl ? 'ssl://' : 'tcp://') . $c['smtp_host'] . ':' . $c['smtp_port'], $errno, $errstr, 10, STREAM_CLIENT_CONNECT, $ctx);
  if (!$sock) return false;
  stream_set_timeout($sock, 10);
  $read = function () use ($sock): string {
    $out = '';
    while (($line = fgets($sock, 1024)) !== false) { $out .= $line; if (!isset($line[3]) || $line[3] !== '-') break; }
    return $out;
  };
  $cmd = function (string $line, string $expect) use ($sock, $read): bool {
    fwrite($sock, $line . "\r\n");
    return strpos($read(), $expect) === 0;
  };
  if (strpos($read(), '220') !== 0) { fclose($sock); return false; }
  $host = $_SERVER['SERVER_NAME'] ?? 'markentrix.de';
  if (!$cmd('EHLO ' . $host, '250')) { fclose($sock); return false; }
  if ($sec === 'tls') {
    if (!$cmd('STARTTLS', '220') || !@stream_socket_enable_crypto($sock, true, STREAM_CRYPTO_METHOD_TLS_CLIENT)) { fclose($sock); return false; }
    if (!$cmd('EHLO ' . $host, '250')) { fclose($sock); return false; }
  }
  $ok = ($c['smtp_user'] === '' || ($cmd('AUTH LOGIN', '334') && $cmd(base64_encode($c['smtp_user']), '334') && $cmd(base64_encode($c['smtp_pass']), '235')))
     && $cmd('MAIL FROM:<' . $c['from'] . '>', '250') && $cmd('RCPT TO:<' . $to . '>', '250') && $cmd('DATA', '354');
  if ($ok) {
    $msg = implode("\r\n", array_merge(['To: ' . $to, 'Subject: ' . $subject, 'Date: ' . date(DATE_RFC2822)], $headers)) . "\r\n\r\n"
         . preg_replace('/^\./m', '..', str_replace("\n", "\r\n", $body));
    fwrite($sock, $msg . "\r\n.\r\n");
    $ok = strpos($read(), '250') === 0;
  }
  @fwrite($sock, "QUIT\r\n");
  fclose($sock);
  return $ok;
}

/** Versand über SMTP oder mail(), je nach Konfiguration. */
function deliver(array $c, string $to, string $encodedSubject, string $body, array $headers): bool {
  if ($c['smtp_host'] !== '') return smtp_send($c, $to, $encodedSubject, $body, $headers);
  return @mail($to, $encodedSubject, $body, implode("\r\n", $headers), '-f' . $c['from']);
}
