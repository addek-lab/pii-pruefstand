"""Beispiel: eigenen Filter in den Prüfstand einhängen.

    python -m pruefstand run --plugin examples/eigener_filter.py:detect --html bericht.html

Die Funktion bekommt den Text und liefert eine Liste von (start, end, label).
Bekannte Labels: PERSON, ADRESSE, PLZ_ORT, GEBURTSDATUM, TELEFON, EMAIL, IBAN, BIC, KREDITKARTE,
STEUER_ID, KVNR, ICD10, DIAGNOSE, MEDIKAMENT. Alles andere zählt als "OTHER" (wird bei der
Abdeckung mitgezählt, aber nicht beim Typ).
"""
import re


def detect(text):
    return [(m.start(), m.end(), "EMAIL")
            for m in re.finditer(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)]
