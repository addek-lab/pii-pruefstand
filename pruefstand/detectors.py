"""Erkennungsverfahren, die im Prüfstand gegeneinander antreten.

Jeder Detektor ist eine Funktion  detect(text) -> list[Span].
Eigene Verfahren lassen sich per Plugin einhängen (siehe load_plugin).
"""
from __future__ import annotations

import importlib.util
import os
import re

from . import data, validators
from .core import Span

U = "A-ZÄÖÜÇŞİĞ"
L = "a-zäöüßçşığ"


# ------------------------------------------------------------------ Hilfen
def _context(text: str, start: int, words, window: int) -> bool:
    before = text[max(0, start - window):start].lower()
    return any(w in before for w in words)


def _find(pattern, text, label, validate=None, group=0, flags=0):
    for m in re.finditer(pattern, text, flags):
        value = m.group(group)
        if validate and not validate(m, value):
            continue
        yield Span(m.start(group), m.end(group), label)


PRIORITY = {"IBAN": 0, "KREDITKARTE": 0, "STEUER_ID": 0, "KVNR": 0, "BIC": 0, "EMAIL": 0}


def resolve(spans):
    """Entfernt Überlappungen: Kennungen mit Prüfsumme zuerst, dann längere Treffer."""
    order = sorted(spans, key=lambda s: (PRIORITY.get(s.label, 1), -s.length(), s.start))
    kept = []
    for s in order:
        if all(s.end <= k.start or s.start >= k.end for k in kept):
            kept.append(s)
    return sorted(kept, key=lambda s: s.start)


# ------------------------------------------------------------------ Detektor 1: einfacher Regex-Filter
def detect_naiv(text: str):
    """So arbeiten viele schnelle Filter: ein paar Muster, keine Prüfsummen, kein Kontext."""
    out = []
    out += _find(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text, "EMAIL")
    out += _find(r"DE\d{20}", text, "IBAN")
    out += _find(r"(?<!\d)\d{16}(?!\d)", text, "KREDITKARTE")
    out += _find(r"(?<!\d)(?:\+49|0)[\d /()\-]{8,}\d", text, "TELEFON")
    return resolve(out)


# ------------------------------------------------------------------ Detektor 2: Referenz-Regeln
_DATE = (r"\d{1,2}\.(?:\d{1,2}\.|\s?(?:Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|"
         r"November|Dezember)\s)\d{4}")
_NAME = rf"[{U}][{L}\-]+(?:[ ][{U}][{L}\-]+){{0,2}}"
_GAZ_NAMES = "|".join(data.GAZETTEER_FIRST_NAMES)
_GAZ_MEDS = "|".join(data.GAZETTEER_MEDICATIONS)
_GAZ_DX = "|".join(re.escape(d) for d in data.GAZETTEER_DIAGNOSES)
_PLZ_STOP = {"Euro", "Mal", "Uhr", "Stück", "Prozent"}


def detect_referenz(text: str):
    """Regeln mit Prüfsummen und Kontext für deutsche Finanz- und Gesundheitsdaten."""
    out = []
    out += _find(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text, "EMAIL")
    out += _find(r"(?<![A-Za-z0-9])DE\d{2}(?: ?\d{4}){4} ?\d{2}(?!\d)", text, "IBAN",
                 validate=lambda m, v: validators.iban_valid(v))
    out += _find(r"(?<![A-Za-z0-9])[A-Z]{4}DE[A-Z0-9]{2}(?:[A-Z0-9]{3})?(?![A-Za-z0-9])", text, "BIC",
                 validate=lambda m, v: _context(text, m.start(), ("bic", "swift"), 14))
    out += _find(r"(?<![\d-])(?:\d{4}[ -]?){3}\d{4}(?![\d-])", text, "KREDITKARTE",
                 validate=lambda m, v: validators.luhn_valid(v))
    out += _find(r"(?<!\d)(?:\d{11}|\d{2} \d{3} \d{3} \d{3})(?!\d)", text, "STEUER_ID",
                 validate=lambda m, v: validators.steuerid_valid(v))
    out += _find(r"(?<![A-Za-z0-9])[A-Z]\d{9}(?![A-Za-z0-9])", text, "KVNR",
                 validate=lambda m, v: validators.kvnr_valid(v) or _context(
                     text, m.start(), ("versichert", "kvnr", "krankenkasse", "krankenversicher"), 40))
    # Telefon
    out += _find(r"(?<![\d+])(?:\+49|0049) ?(?:\(0\) ?)?\d{2,5}[ /-]?\d{3,9}(?!\d)", text, "TELEFON")
    out += _find(r"(?<![\d+(])0\d{2,4}[ /-]\d{3,9}(?: \d{2,4})?(?!\d)", text, "TELEFON")
    out += _find(r"\(0\d{1,4}\) ?\d{3,5}[ -]?\d{2,6}(?!\d)", text, "TELEFON")
    # Geburtsdatum nur mit Kontext (sonst wären alle Termine betroffen)
    out += _find(_DATE, text, "GEBURTSDATUM",
                 validate=lambda m, v: _context(text, m.start(), ("geb", "geboren", "geburtsdatum"), 22))
    # Adresse, PLZ + Ort
    out += _find(rf"(?<![A-Za-z{L}{U}])(?:[{U}][{L}]+(?:straße|strasse|weg|platz|allee|gasse|ring|damm|ufer)"
                 rf"|[{U}][{L}]+ (?:Allee|Markt|Platz))[ ]\d{{1,3}}[a-z]?(?![\dA-Za-z])", text, "ADRESSE")
    out += _find(rf"(?<!\d)\d{{5}}[ ]+[{U}][{L}]+(?:\-[{U}][{L}]+)?(?:[ ](?:am|an der)[ ][{U}][{L}]+)?", text, "PLZ_ORT",
                 validate=lambda m, v: v.split()[1] not in _PLZ_STOP)
    # Gesundheit
    out += _find(r"(?<![A-Za-z0-9])[A-TV-Z]\d{2}(?:\.\d{1,2})?(?![A-Za-z0-9])", text, "ICD10",
                 validate=lambda m, v: _context(text, m.start(), ("icd", "diagnose"), 40))
    out += _find(rf"(?<![A-Za-z{L}{U}])(?:{_GAZ_DX})(?![A-Za-z{L}])", text, "DIAGNOSE", flags=re.IGNORECASE)
    out += _find(rf"(?<![A-Za-z{L}{U}])(?:{_GAZ_MEDS})(?![A-Za-z{L}])", text, "MEDIKAMENT")
    # Personen: Kontext (Herr/Frau/Patient...) oder bekannter Vorname + Nachname
    out += _find(rf"(?:Herr|Frau|Dr\.|Prof\.|Patient(?:in)?|Versicherte(?:\(r\)|r)?|Kontoinhaber(?:in)?|Name|Name ist)"
                 rf"[: ]+({_NAME})", text, "PERSON", group=1)
    out += _find(rf"(?<![A-Za-z{L}{U}])(?:{_GAZ_NAMES})[ ][{U}][{L}]+(?:\-[{U}][{L}]+)?", text, "PERSON")
    return resolve(out)


# ------------------------------------------------------------------ Plugins
BUILTIN = {
    "naiv": ("Einfacher Regex-Filter", detect_naiv),
    "referenz": ("Referenz-Regeln (Prüfsumme + Kontext)", detect_referenz),
}


def load_plugin(spec: str):
    """spec = 'pfad/zur/datei.py:funktion'. Die Funktion bekommt den Text und liefert eine Liste
    von (start, end, label)-Tupeln oder Span-Objekten. Unbekannte Labels zählen als 'OTHER'."""
    # Windows-Pfade enthalten selbst einen Doppelpunkt (C:\...), daher nur am LETZTEN trennen
    # und nur, wenn dahinter ein Funktionsname und kein Pfadteil steht.
    path, sep, func = spec.rpartition(":")
    if not sep or "\\" in func or "/" in func or not func.isidentifier():
        path, func = spec, "detect"
    modspec = importlib.util.spec_from_file_location("pruefstand_plugin", path)
    mod = importlib.util.module_from_spec(modspec)
    modspec.loader.exec_module(mod)
    fn = getattr(mod, func)

    def wrapped(text):
        spans = []
        for item in fn(text):
            if isinstance(item, Span):
                spans.append(item)
            else:
                s, e, lab = item
                spans.append(Span(int(s), int(e), lab if lab in data.LABEL_DE else "OTHER"))
        return spans

    name = f"Plugin: {os.path.basename(path)}:{func}"
    return name, wrapped
