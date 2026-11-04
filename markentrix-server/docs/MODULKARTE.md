# Modulkarte des Portals

Wird von `tools/struktur.py --karte` erzeugt. **Nicht von Hand ändern.** Die Gruppen stehen in `tools/struktur_gruppen.json`.
Schichten: 1 Grundlagen, 2 Fachlogik, 3 Routen, 4 Start. Ein Modul darf beim Laden nur Module aus gleicher oder niedrigerer Schicht importieren. Verzögerte Importe in Funktionen sind erlaubt.

## Grundlagen (`kern`)

Datenbank, Sicherheit, Einstellungen, Mail, PDF, Dateien, KI und Push. Von allen anderen Bereichen genutzt, nutzt selbst keinen Fachbereich.

| Modul | Schicht | Zeilen | Genutzt von |
|---|---|---|---|
| `__init__` | 1 | 0 | – |
| `betrieb` | 1 | 29 | `cli`, `jobs`, `ki`, `mailer` und 2 weitere |
| `config` | 1 | 31 | `angebotserinnerung`, `angebotsfluss`, `aufgabendetail`, `db` und 45 weitere |
| `dateien` | 1 | 94 | `routes_freigabelink`, `routes_zusammenarbeit` |
| `db` | 1 | 34 | `abo`, `angebotserinnerung`, `angebotsgrund`, `betrieb` und 146 weitere |
| `einstellungen` | 1 | 54 | `angebotserinnerung`, `cli`, `domaincheck`, `funnelcheck` und 37 weitere |
| `fehlerhilfe` | 1 | 142 | `jobs`, `main`, `routes_system`, `sitedienste` und 1 weitere |
| `ki` | 1 | 257 | `routes_admin`, `routes_angebotsinhalte`, `routes_einstellungen`, `routes_kunde` und 3 weitere |
| `mailer` | 1 | 492 | `abo`, `angebotserinnerung`, `angebotsfluss`, `cli` und 34 weitere |
| `mailvorlage` | 1 | 310 | `mailer`, `routes_sitedienste`, `sitedienste`, `t95.py` |
| `pdf` | 1 | 156 | `anleitung_pdf`, `avv`, `belege`, `berichte` und 5 weitere |
| `push` | 1 | 176 | `abo`, `angebotserinnerung`, `angebotsfluss`, `domaincheck` und 26 weitere |
| `security` | 1 | 247 | `angebotserinnerung`, `angebotsfluss`, `angebotsgrund`, `cli` und 77 weitere |
| `zustellung` | 1 | 114 | `jobs`, `mailer`, `routes_betriebplus`, `sitedienste` und 1 weitere |

## Anmeldung und Zugänge (`zugang`)

Einladungen, Passwort-Zurücksetzen, Zwei-Faktor, Passkeys, Anmelde-Links, Team-Zugänge und Mitarbeiter-Rechte.

| Modul | Schicht | Zeilen | Genutzt von |
|---|---|---|---|
| `passkey` | 2 | 168 | `routes_passkey` |
| `zugang` | 2 | 41 | `routes_admin`, `routes_mitarbeiter`, `routes_team`, `routes_verwaltung` |
| `zweifaktor` | 2 | 70 | `routes_2fa`, `routes_auth`, `t63.py`, `t8.py` |
| `routes_2fa` | 3 | 142 | `main` |
| `routes_auth` | 3 | 147 | `main` |
| `routes_loginlink` | 3 | 63 | `main` |
| `routes_mitarbeiter` | 3 | 71 | `main` |
| `routes_passkey` | 3 | 128 | `main` |
| `routes_team` | 3 | 164 | `main` |

## Kunden-Websites (`website`)

Website-API, Terminbuchung, Online-Shop, Gutscheine, Upload, Domains, Statusseite und Livegang-Prüfungen.

| Modul | Schicht | Zeilen | Genutzt von |
|---|---|---|---|
| `buchungsvorlagen` | 2 | 63 | `routes_buchungsvorlagen` |
| `domaincheck` | 2 | 244 | `jobs`, `routes_websites` |
| `fotos` | 2 | 212 | `jobs`, `offboarding`, `routes_kunde`, `routes_shop` und 2 weitere |
| `livecheck` | 2 | 187 | `routes_webupload`, `webbetrieb` |
| `publish` | 2 | 221 | `routes_admin`, `routes_angebotsinhalte`, `routes_domains`, `routes_kunde` |
| `shop` | 2 | 132 | `routes_shop` |
| `sitedienste` | 2 | 870 | `funnelcheck`, `routes_betriebplus`, `routes_buchungsvorlagen`, `routes_leistungsfreigabe` und 8 weitere |
| `webbetrieb` | 2 | 552 | `berichte`, `domaincheck`, `jobs`, `routes_kundenampel` und 6 weitere |
| `routes_angebotsinhalte` | 3 | 221 | `main` |
| `routes_buchungsvorlagen` | 3 | 47 | `main` |
| `routes_domains` | 3 | 124 | `main` |
| `routes_referenzseite` | 3 | 91 | `main` |
| `routes_shop` | 3 | 744 | `main`, `routes_siteapi` |
| `routes_siteapi` | 3 | 579 | `main`, `routes_shop`, `t95.py` |
| `routes_sitedienste` | 3 | 2273 | `main`, `routes_buchungsvorlagen`, `routes_leistungsfreigabe`, `routes_shop` und 2 weitere |
| `routes_status` | 3 | 127 | `main`, `routes_plattformstatus` |
| `routes_websites` | 3 | 252 | `main`, `routes_betriebplus`, `routes_offboarding`, `routes_webupload` |
| `routes_webupload` | 3 | 496 | `main` |

## Lead-Funnel und Website-Check (`funnel`)

Kampagnenseiten, Website-Check, Funnel-Mails und Folgemails an Leads.

| Modul | Schicht | Zeilen | Genutzt von |
|---|---|---|---|
| `funnelcheck` | 2 | 627 | `funnelmail`, `jobs`, `routes_funnel` |
| `funnelmail` | 2 | 161 | `funnelcheck`, `mailer` |
| `routes_folgemails` | 3 | 97 | `funnelcheck`, `jobs`, `main` |
| `routes_funnel` | 3 | 572 | `main` |
| `routes_websitecheck` | 3 | 160 | `main` |

## Vertrieb (`vertrieb`)

Leads, Zuweisung, Sperrliste, Gesprächsleitfaden, Anruf-Modus, Erstgespräche, Rangliste und Vertriebs-Auswertung.

| Modul | Schicht | Zeilen | Genutzt von |
|---|---|---|---|
| `anrufzeiten` | 2 | 62 | `routes_vertrieb`, `routes_vertriebfluss`, `routes_verwaltung`, `t120.py` |
| `heissleads` | 2 | 46 | `routes_vertriebsplus` |
| `kalenderabo` | 2 | 92 | `main` |
| `leadeingang` | 2 | 24 | `routes_buchung`, `routes_funnel`, `routes_websitecheck` |
| `leadkontakt` | 2 | 85 | `jobs`, `routes_vertrieb`, `routes_vertriebsplus`, `routes_verwaltung` und 1 weitere |
| `leadpruefung` | 2 | 51 | `routes_vertrieb`, `routes_verwaltung` |
| `leitfaden` | 2 | 173 | `routes_vertriebwerkzeuge` |
| `sperre` | 2 | 64 | `funnelcheck`, `jobs`, `leadkontakt`, `leadpruefung` und 5 weitere |
| `visitenkarte` | 2 | 186 | `main` |
| `zuweisung` | 2 | 39 | `jobs`, `leadeingang`, `routes_leadimport`, `routes_leadsteuerung` und 2 weitere |
| `routes_buchung` | 3 | 225 | `jobs`, `main`, `routes_leadtermin` |
| `routes_leadimport` | 3 | 261 | `main` |
| `routes_leadsteuerung` | 3 | 70 | `main` |
| `routes_leadtermin` | 3 | 81 | `main` |
| `routes_rangliste` | 3 | 69 | `main` |
| `routes_vertrieb` | 3 | 234 | `main`, `routes_leadtermin`, `routes_vertriebwerkzeuge`, `vertriebangebot` und 1 weitere |
| `routes_vertriebfluss` | 3 | 132 | `main` |
| `routes_vertriebqualitaet` | 3 | 93 | `main` |
| `routes_vertriebsplus` | 3 | 158 | `main` |
| `routes_vertriebwerkzeuge` | 3 | 232 | `main` |

## Angebote, Rechnungen, Zahlung (`geld`)

Angebote, Rechnungen, Quittungen, Wartungsverträge, Zahlungsabgleich, SEPA, Preisänderung, Provisionen und Pakete.

| Modul | Schicht | Zeilen | Genutzt von |
|---|---|---|---|
| `abo` | 2 | 118 | `jobs`, `routes_betriebplus`, `t57.py` |
| `angebotserinnerung` | 2 | 248 | `jobs`, `main`, `routes_belege`, `routes_leadangebot` |
| `angebotsfluss` | 2 | 35 | `routes_belege`, `routes_leadangebot` |
| `angebotsgrund` | 2 | 51 | `main`, `routes_angebotsplus`, `routes_belege`, `routes_leadangebot` |
| `belege` | 2 | 180 | `abo`, `angebotserinnerung`, `offboarding`, `routes_belege` und 3 weitere |
| `preisaenderung` | 2 | 257 | `jobs`, `main` |
| `quittung` | 2 | 26 | `routes_sitedienste` |
| `vertriebangebot` | 2 | 276 | `main` |
| `zahlungsabgleich` | 2 | 98 | `routes_belege` |
| `routes_angebotsplus` | 3 | 122 | `main` |
| `routes_belege` | 3 | 460 | `main`, `routes_werkzeuge` |
| `routes_leadangebot` | 3 | 320 | `angebotserinnerung`, `main`, `routes_angebotsplus`, `vertriebangebot` und 1 weitere |
| `routes_pakete` | 3 | 211 | `main`, `tipps` |
| `routes_provision` | 3 | 181 | `main` |
| `routes_zahlung` | 3 | 312 | `jobs`, `main`, `t25.py` |

## Verträge und Datenschutz (`recht`)

AVV, Verträge, Datenschutz-Anfragen (DSGVO), Rechtstexte, Unterauftragsverarbeiter und Vertragsende.

| Modul | Schicht | Zeilen | Genutzt von |
|---|---|---|---|
| `avv` | 2 | 160 | `routes_avv`, `routes_system`, `routes_uav` |
| `avv_text` | 2 | 192 | `avv` |
| `offboarding` | 2 | 180 | `routes_betriebplus`, `routes_offboarding` |
| `rechtstexte` | 2 | 75 | `abo`, `angebotserinnerung`, `belege`, `berichte` und 12 weitere |
| `vertraege` | 2 | 144 | `routes_vertraege`, `routes_vertragportal` |
| `routes_avv` | 3 | 426 | `main`, `routes_admin`, `routes_aufgaben`, `routes_system` |
| `routes_dsgvo` | 3 | 200 | `main` |
| `routes_offboarding` | 3 | 63 | `main` |
| `routes_public` | 3 | 13 | `main` |
| `routes_uav` | 3 | 129 | `main` |
| `routes_vertraege` | 3 | 369 | `main`, `routes_vertragportal` |
| `routes_vertragportal` | 3 | 266 | `main`, `routes_vertraege` |

## Kundenportal und Betreuung (`kunde`)

Heute-Seite, Anfragen, Briefing, Onboarding, Zusammenarbeit, Wissen, Berichte, Diagramme, Telefon-Assistent und Hilfe.

| Modul | Schicht | Zeilen | Genutzt von |
|---|---|---|---|
| `anleitung_pdf` | 2 | 72 | `routes_hilfe`, `zugang` |
| `aufgabendetail` | 2 | 68 | `jobs`, `t96.py` |
| `berichte` | 2 | 229 | `jobs`, `offboarding`, `routes_admin`, `routes_briefing` und 2 weitere |
| `branchenvorlagen` | 2 | 130 | `routes_vorlagen` |
| `diagramme` | 2 | 32 | `routes_diagramme` |
| `ersteswoche` | 2 | 47 | `main` |
| `kundenwerkzeuge` | 2 | 32 | `routes_kundenwerkzeuge` |
| `onboarding` | 2 | 135 | `aufgabendetail`, `routes_admin`, `routes_diagramme`, `routes_kunde` und 3 weitere |
| `tagesblick` | 2 | 66 | `jobs`, `routes_dashboard` |
| `tipps` | 2 | 101 | `main` |
| `routes_aufgaben` | 3 | 252 | `main`, `routes_admin` |
| `routes_briefing` | 3 | 181 | `main` |
| `routes_diagramme` | 3 | 131 | `main` |
| `routes_freigabelink` | 3 | 78 | `main` |
| `routes_fruehwarnung` | 3 | 101 | `jobs`, `main`, `routes_dashboard`, `t67.py` |
| `routes_hilfe` | 3 | 83 | `main` |
| `routes_kunde` | 3 | 592 | `main` |
| `routes_kundenampel` | 3 | 69 | `main` |
| `routes_kundenwerkzeuge` | 3 | 269 | `main` |
| `routes_onboarding` | 3 | 131 | `main` |
| `routes_telefon` | 3 | 210 | `main` |
| `routes_umfrage` | 3 | 117 | `jobs`, `main` |
| `routes_vorlagen` | 3 | 54 | `main` |
| `routes_wert` | 3 | 56 | `main` |
| `routes_wissen` | 3 | 329 | `main` |
| `routes_zusammenarbeit` | 3 | 711 | `angebotsfluss`, `jobs`, `main`, `routes_angebotsinhalte` und 18 weitere |

## Admin und Betrieb (`admin`)

Kunden- und Systemverwaltung, Einstellungen, Dashboard, Werkzeuge, Systemstatus und Nutzungsmessung.

| Modul | Schicht | Zeilen | Genutzt von |
|---|---|---|---|
| `routes_admin` | 3 | 543 | `main`, `routes_verwaltung` |
| `routes_betriebplus` | 3 | 541 | `main` |
| `routes_dashboard` | 3 | 291 | `jobs`, `main` |
| `routes_einstellungen` | 3 | 195 | `main` |
| `routes_leistungsfreigabe` | 3 | 89 | `main` |
| `routes_nutzung` | 3 | 52 | `jobs`, `main` |
| `routes_plattformstatus` | 3 | 182 | `main` |
| `routes_push` | 3 | 64 | `main` |
| `routes_system` | 3 | 231 | `jobs`, `main`, `t73.py` |
| `routes_verwaltung` | 3 | 766 | `jobs`, `main` |
| `routes_werkzeuge` | 3 | 319 | `main` |

## Start und Hintergrund (`start`)

Programmstart, Kommandozeile und Hintergrundaufgaben. Dürfen alles laden, werden von Fachbereichen nicht importiert.

| Modul | Schicht | Zeilen | Genutzt von |
|---|---|---|---|
| `cli` | 4 | 182 | `install.sh`, `mkctl`, `selbsttest.sh`, `t29.py` und 2 weitere |
| `jobs` | 4 | 1309 | `main`, `routes_admin`, `routes_einstellungen`, `t108.py` und 8 weitere |
| `main` | 4 | 293 | `smoke.py`, `t16.py`, `t28.py`, `t41.py` und 1 weitere |

