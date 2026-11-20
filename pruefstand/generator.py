"""Erzeugt synthetische deutsche Dokumente (Finanz und Gesundheit) mit exakten Gold-Annotationen.

Alle Personen, Nummern und Adressen sind erfunden bzw. zufällig. Die Dokumente enthalten
absichtlich auch Störgrößen (Termine, Beträge, Auftragsnummern), die KEINE personenbezogenen
Daten sind. So lassen sich Falschalarme messen.
"""
from __future__ import annotations

import random

from . import data, validators
from .core import Doc, Span


class _Builder:
    def __init__(self):
        self.parts = []

    def t(self, text):
        self.parts.append((text, None))
        return self

    def s(self, label, value):
        self.parts.append((value, label))
        return self

    def build(self, doc_id, kind) -> Doc:
        text, spans = "", []
        for value, label in self.parts:
            if label:
                spans.append(Span(len(text), len(text) + len(value), label))
            text += value
        return Doc(doc_id, kind, text, spans)


# ------------------------------------------------------------------ Werte
def _ascii(s: str) -> str:
    table = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss", "ç": "c", "ş": "s", "ı": "i", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "Ç": "C"}
    return "".join(table.get(c, c) for c in s).lower()


def _name(rng):
    return rng.choice(data.FIRST_NAMES), rng.choice(data.LAST_NAMES)


def _dob(rng):
    y, m, d = rng.randint(1940, 2004), rng.randint(1, 12), rng.randint(1, 28)
    style = rng.randint(0, 2)
    if style == 0:
        return f"{d:02d}.{m:02d}.{y}"
    if style == 1:
        return f"{d}.{m}.{y}"
    return f"{d}. {data.MONTHS[m - 1]} {y}"


def _noise_date(rng):
    return f"{rng.randint(1, 28):02d}.{rng.randint(1, 12):02d}.{rng.choice([2026, 2027])}"


def _phone(rng):
    mobile = rng.choice(["151", "160", "170", "172", "176"])
    area = rng.choice(["30", "40", "89", "221", "69", "711", "341"])
    n7 = f"{rng.randint(1000000, 9999999)}"
    n8 = f"{rng.randint(10000000, 99999999)}"
    return rng.choice([
        f"+49 {mobile} {n8}", f"0{mobile} {n8}", f"0{mobile}/{n8}", f"0{area} {n7}",
        f"(0{area}) {n7[:4]} {n7[4:]}", f"+49 (0){area} {n7}", f"0{area}/{n7}",
    ])


def _email(rng, fn, ln):
    sep = rng.choice([".", "_", ""])
    return f"{_ascii(fn)}{sep}{_ascii(ln)}@{rng.choice(['example.org', 'example.com', 'mail.example'])}"


def _address(rng):
    return f"{rng.choice(data.STREETS)} {rng.randint(1, 120)}{rng.choice(['', '', '', 'a', 'b'])}"


def _amount(rng, lo=20, hi=25000):
    v = rng.randint(lo * 100, hi * 100) / 100
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} €"


def _plz_ort(rng):
    city, plz = rng.choice(data.CITIES)
    return f"{plz} {city}"


# ------------------------------------------------------------------ Vorlagen
def _arztbrief(rng, i):
    fn, ln = _name(rng)
    icd, dx = rng.choice(data.DIAGNOSES)
    med = rng.choice(data.MEDICATIONS)
    b = _Builder().t("Praxis Dr. ").s("PERSON", rng.choice(data.LAST_NAMES)).t("\nArztbrief\n\n")
    b.t(rng.choice(["Patient: ", "Patientin: ", "Name: "])).s("PERSON", f"{fn} {ln}").t("\n")
    b.t(rng.choice(["geb. ", "Geburtsdatum: ", "geboren am "])).s("GEBURTSDATUM", _dob(rng)).t("\n")
    b.t(rng.choice(["Versichertennummer: ", "KVNR: ", "Krankenversichertennummer "])).s("KVNR", validators.make_kvnr(rng)).t("\n")
    b.t("Anschrift: ").s("ADRESSE", _address(rng)).t(", ").s("PLZ_ORT", _plz_ort(rng)).t("\n\n")
    b.t("Diagnose: ").s("ICD10", icd).t(" (").s("DIAGNOSE", dx).t(")\n")
    b.t("Medikation: ").s("MEDIKAMENT", med).t(f" {rng.choice([5, 20, 40, 50, 500])} mg {rng.choice(['1-0-0', '1-0-1', '0-0-1'])}\n")
    b.t(f"Kontrolltermin am {_noise_date(rng)}.\n")
    if rng.random() < 0.7:
        b.t("Rückfragen unter ").s("TELEFON", _phone(rng)).t(".")
    return b.build(i, "arztbrief")


def _ueberweisung(rng, i):
    fn, ln = _name(rng)
    sender = _name(rng)
    iban = validators.format_iban(validators.make_iban(rng), rng.random() < 0.7)
    b = _Builder().t(rng.choice(["Hallo, ", "Guten Tag, ", "Hi, "]))
    b.t(f"bitte überweise {_amount(rng)} an ").s("PERSON", f"{fn} {ln}").t(".\n")
    b.t(rng.choice(["IBAN: ", "Konto: ", "IBAN "])).s("IBAN", iban).t("\n")
    if rng.random() < 0.8:
        bic = "".join(rng.choice("ABCDEFGHKLMNPRSTUVW") for _ in range(4)) + "DE" + rng.choice(["FF", "M1", "B2", "HH"])
        if rng.random() < 0.5:
            bic += "XXX"
        b.t("BIC: ").s("BIC", bic).t("\n")
    b.t(f"Verwendungszweck: Rechnung {rng.randint(1000000000, 9999999999)}")
    if rng.random() < 0.5:  # Störgröße: sieht aus wie eine Versichertennummer, ist aber eine Artikelnummer
        b.t(f", Artikel {rng.choice('ABCDEFGHKLMNPRSTUVWXYZ')}{rng.randint(100000000, 999999999)}")
    b.t("\nDanke und Gruß\n").s("PERSON", f"{sender[0]} {sender[1]}")
    return b.build(i, "ueberweisung")


def _kreditantrag(rng, i):
    fn, ln = _name(rng)
    sid = validators.format_steuerid(validators.make_steuerid(rng), rng.random() < 0.3)
    greeting = rng.choice(["Sehr geehrte Damen und Herren", "Sehr geehrter Herr Kundenberater", "Guten Tag"])
    b = _Builder().t(f"Betreff: Kreditantrag\n\n{greeting},\n\nich, ")
    b.s("PERSON", f"{fn} {ln}").t(", ").t(rng.choice(["geboren am ", "geb. "])).s("GEBURTSDATUM", _dob(rng))
    b.t(", wohnhaft ").s("ADRESSE", _address(rng)).t(", ").s("PLZ_ORT", _plz_ort(rng))
    b.t(f", beantrage ein Darlehen über {_amount(rng, 2000, 60000)}.\n")
    b.t(rng.choice(["Meine Steuer-ID lautet ", "Steuer-ID: ", "Steuerliche Identifikationsnummer: "])).s("STEUER_ID", sid).t(".\n")
    b.t(f"Mein monatliches Netto beträgt {_amount(rng, 1200, 6500)}.\n")
    b.t("Gehaltskonto: ").s("IBAN", validators.format_iban(validators.make_iban(rng), True)).t("\n")
    b.t("Erreichbar unter ").s("EMAIL", _email(rng, fn, ln))
    if rng.random() < 0.6:
        b.t(" oder ").s("TELEFON", _phone(rng))
    b.t(".\n\nMit freundlichen Grüßen")
    return b.build(i, "kreditantrag")


def _support(rng, i):
    fn, ln = _name(rng)
    card = validators.format_card(validators.make_card(rng), rng.randint(0, 2))
    b = _Builder().t("Support-Ticket\n\nMeine Karte ").s("KREDITKARTE", card).t(" wurde abgelehnt")
    b.t(f" (Auftrag-Nr. {rng.randint(1000000000, 9999999999)}, Betrag {_amount(rng, 5, 900)}).\n")
    b.t(f"Bitte rufen Sie mich am {_noise_date(rng)} zurück: ").s("TELEFON", _phone(rng)).t(".\n")
    if rng.random() < 0.5:  # Störgröße: Hotline des Anbieters ist keine personenbezogene Angabe
        b.t(f"(Ihre Servicehotline: 0800 {rng.randint(1000000, 9999999)})\n")
    b.t(rng.choice(["Viele Grüße, ", "Gruß ", "Danke, "])).s("PERSON", f"{fn} {ln}")
    return b.build(i, "support")


def _kasse(rng, i):
    fn, ln = _name(rng)
    icd, dx = rng.choice(data.DIAGNOSES)
    b = _Builder().t("Antrag auf Kostenübernahme\n\nVersicherte(r): ").s("PERSON", f"{fn} {ln}").t(", ")
    b.t("KVNR ").s("KVNR", validators.make_kvnr(rng)).t(f", Aktenzeichen {rng.randint(100000, 999999)}\n")
    b.t("Diagnose laut ICD-10: ").s("ICD10", icd).t(", ").s("DIAGNOSE", dx).t("\n")
    b.t("Verordnet: ").s("MEDIKAMENT", rng.choice(data.MEDICATIONS)).t(".\n")
    b.t("Rückruf: ").s("TELEFON", _phone(rng))
    return b.build(i, "kasse")


def _kontoauszug(rng, i):
    b = _Builder().t("Kontoauszug\n")
    for _ in range(rng.randint(2, 3)):
        fn, ln = _name(rng)
        b.t(f"{_noise_date(rng)[:6]} Überweisung an ").s("PERSON", f"{fn} {ln}").t(", ")
        b.s("IBAN", validators.format_iban(validators.make_iban(rng), rng.random() < 0.6))
        b.t(f", -{_amount(rng, 10, 3000)}\n")
    return b.build(i, "kontoauszug")


def _beschwerde(rng, i):
    fn, ln = _name(rng)
    b = _Builder().t("Beschwerde\n\nGuten Tag, mein Name ist ").s("PERSON", f"{fn} {ln}").t(" (")
    b.s("GEBURTSDATUM", _dob(rng)).t(") aus ").s("PLZ_ORT", _plz_ort(rng)).t(".\n")
    b.t("Meine Krankenkassen-Nr. ").s("KVNR", validators.make_kvnr(rng)).t(" wird nicht akzeptiert, ")
    b.t("und die Abbuchung von ").s("IBAN", validators.format_iban(validators.make_iban(rng), False)).t(f" war {_amount(rng, 20, 800)}.\n")
    b.t("Mein Arzt sagt, ich habe ").s("DIAGNOSE", rng.choice(data.DIAGNOSES)[1]).t(".\n")
    b.t("Antwort bitte an ").s("EMAIL", _email(rng, fn, ln)).t(".")
    return b.build(i, "beschwerde")


_TEMPLATES = [
    (_arztbrief, 3), (_ueberweisung, 3), (_kreditantrag, 2), (_support, 2),
    (_kasse, 2), (_kontoauszug, 2), (_beschwerde, 2),
]


def generate(n: int, seed: int = 1) -> list[Doc]:
    """Erzeugt n Dokumente. Gleicher Seed ergibt exakt dieselben Dokumente."""
    rng = random.Random(seed)
    funcs = [f for f, w in _TEMPLATES for _ in range(w)]
    return [rng.choice(funcs)(rng, i) for i in range(n)]
