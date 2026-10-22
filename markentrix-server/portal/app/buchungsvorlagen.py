"""Startpakete für die Terminbuchung je Branche: Leistungen (zunächst INAKTIV und ohne Preis, damit nichts Falsches live geht),
Zusatzfragen und typische Arbeitszeiten. Der Betrieb oder das Team trägt Preise ein und schaltet die Leistungen frei."""

BUCHUNGSVORLAGEN = {
    "friseur": {
        "name": "Friseur und Beauty",
        "plan": {"2": "09:00-13:00, 14:00-18:00", "3": "09:00-13:00, 14:00-18:00", "4": "09:00-13:00, 14:00-19:00", "5": "09:00-13:00, 14:00-18:00", "6": "09:00-14:00"},
        "leistungen": [
            {"name": "Damenhaarschnitt", "dauer_min": 60, "felder": [{"label": "Haarlänge", "pflicht": True}, {"label": "Haarzustand", "pflicht": False}]},
            {"name": "Herrenhaarschnitt", "dauer_min": 30, "felder": []},
            {"name": "Färben", "dauer_min": 120, "puffer_min": 10, "felder": [{"label": "Haarlänge", "pflicht": True}, {"label": "Letzte Behandlung", "pflicht": True}]},
            {"name": "Strähnen und Balayage", "dauer_min": 180, "freigabe": True, "felder": [{"label": "Haarlänge", "pflicht": True}, {"label": "Letzte Behandlung", "pflicht": True}, {"label": "Wunschfarbe", "pflicht": False}]},
            {"name": "Waschen und Föhnen", "dauer_min": 30, "felder": []},
        ],
    },
    "kfz": {
        "name": "Kfz-Werkstatt",
        "plan": {"1": "07:30-12:00, 13:00-17:00", "2": "07:30-12:00, 13:00-17:00", "3": "07:30-12:00, 13:00-17:00", "4": "07:30-12:00, 13:00-17:00", "5": "07:30-12:00, 13:00-15:00"},
        "leistungen": [
            {"name": "Inspektion", "dauer_min": 120, "freigabe": True, "felder": [{"label": "Kennzeichen", "pflicht": True}, {"label": "Fahrzeugtyp", "pflicht": True}, {"label": "Kilometerstand", "pflicht": False}]},
            {"name": "Reifenwechsel", "dauer_min": 45, "felder": [{"label": "Kennzeichen", "pflicht": True}, {"label": "Reifengröße", "pflicht": False}]},
            {"name": "Ölwechsel", "dauer_min": 45, "felder": [{"label": "Kennzeichen", "pflicht": True}, {"label": "Fahrzeugtyp", "pflicht": True}]},
            {"name": "HU und AU", "dauer_min": 60, "felder": [{"label": "Kennzeichen", "pflicht": True}]},
            {"name": "Fehlerdiagnose", "dauer_min": 60, "freigabe": True, "felder": [{"label": "Kennzeichen", "pflicht": True}, {"label": "Anliegen", "pflicht": True}]},
        ],
    },
    "fahrzeugpflege": {
        "name": "Fahrzeugpflege und Aufbereitung",
        "plan": {"1": "08:00-17:00", "2": "08:00-17:00", "3": "08:00-17:00", "4": "08:00-17:00", "5": "08:00-17:00"},
        "leistungen": [
            {"name": "Außenreinigung", "dauer_min": 90, "felder": [{"label": "Fahrzeug", "pflicht": True}, {"label": "Kennzeichen", "pflicht": False}]},
            {"name": "Innenreinigung", "dauer_min": 150, "felder": [{"label": "Fahrzeug", "pflicht": True}, {"label": "Zustand innen", "pflicht": False}]},
            {"name": "Politur", "dauer_min": 300, "freigabe": True, "felder": [{"label": "Fahrzeug", "pflicht": True}, {"label": "Lackfarbe", "pflicht": False}]},
            {"name": "Keramikversiegelung", "dauer_min": 480, "freigabe": True, "felder": [{"label": "Fahrzeug", "pflicht": True}, {"label": "Lackfarbe", "pflicht": True}]},
        ],
    },
    "kosmetik": {
        "name": "Kosmetik, Nägel und Wellness",
        "plan": {"2": "09:30-18:00", "3": "09:30-18:00", "4": "09:30-19:00", "5": "09:30-18:00", "6": "09:00-14:00"},
        "leistungen": [
            {"name": "Gesichtsbehandlung", "dauer_min": 60, "felder": [{"label": "Hauttyp", "pflicht": False}]},
            {"name": "Maniküre", "dauer_min": 45, "felder": []},
            {"name": "Nagelmodellage", "dauer_min": 90, "felder": [{"label": "Wunschform", "pflicht": False}]},
            {"name": "Wimpernverlängerung", "dauer_min": 120, "freigabe": True, "felder": [{"label": "Letzte Behandlung", "pflicht": False}]},
        ],
    },
    "handwerk": {
        "name": "Handwerk (Beratung vor Ort)",
        "plan": {"1": "08:00-16:00", "2": "08:00-16:00", "3": "08:00-16:00", "4": "08:00-16:00", "5": "08:00-14:00"},
        "leistungen": [
            {"name": "Beratung vor Ort", "dauer_min": 60, "freigabe": True, "felder": [{"label": "Anschrift", "pflicht": True}, {"label": "Anliegen", "pflicht": True}]},
            {"name": "Telefonische Beratung", "dauer_min": 20, "freigabe": False, "felder": [{"label": "Anliegen", "pflicht": True}]},
        ],
    },
    "fitness": {
        "name": "Fitness und Training",
        "plan": {"1": "08:00-20:00", "2": "08:00-20:00", "3": "08:00-20:00", "4": "08:00-20:00", "5": "08:00-18:00", "6": "09:00-13:00"},
        "leistungen": [
            {"name": "Probetraining", "dauer_min": 60, "felder": [{"label": "Trainingsziel", "pflicht": False}]},
            {"name": "Personal Training", "dauer_min": 60, "freigabe": False, "felder": [{"label": "Trainingsziel", "pflicht": False}]},
        ],
    },
}
