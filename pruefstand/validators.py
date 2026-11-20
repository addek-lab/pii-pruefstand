"""Prüfsummen und Generatoren für deutsche Finanz- und Gesundheitskennungen.

Alle erzeugten Werte sind SYNTHETISCH (zufällig, mit gültiger Prüfziffer). Zufällige
Übereinstimmungen mit echten Nummern sind in der Praxis extrem unwahrscheinlich, aber
nicht ausgeschlossen. Es werden nie echte Personendaten verwendet.
"""
from __future__ import annotations

import random
import re


# ----------------------------------------------------------------- IBAN
def iban_valid(value: str) -> bool:
    """Prüft eine IBAN per ISO-7064-Modulo-97 (Länderlänge für DE: 22)."""
    s = re.sub(r"\s+", "", value).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", s):
        return False
    if s.startswith("DE") and len(s) != 22:
        return False
    moved = s[4:] + s[:4]
    digits = "".join(str(int(ch, 36)) for ch in moved)
    return int(digits) % 97 == 1


def make_iban(rng: random.Random) -> str:
    bban = f"{rng.randint(10000000, 99999999)}{rng.randint(0, 9999999999):010d}"
    check = 98 - int(bban + "131400") % 97
    return f"DE{check:02d}{bban}"


def format_iban(iban: str, spaced: bool) -> str:
    return " ".join(iban[i:i + 4] for i in range(0, len(iban), 4)) if spaced else iban


# ----------------------------------------------------------------- Kreditkarte (Luhn)
def luhn_valid(value: str) -> bool:
    digits = [int(c) for c in re.sub(r"[\s-]", "", value) if c.isdigit()]
    if not 12 <= len(digits) <= 19:
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def make_card(rng: random.Random) -> str:
    prefix = rng.choice(["4", "51", "52", "53", "54", "55"])
    body = prefix + "".join(str(rng.randint(0, 9)) for _ in range(15 - len(prefix)))
    total = 0
    for i, ch in enumerate(reversed(body)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return body + str((10 - total % 10) % 10)


def format_card(card: str, style: int) -> str:
    groups = [card[i:i + 4] for i in range(0, 16, 4)]
    return [" ".join(groups), "-".join(groups), card][style % 3]


# ----------------------------------------------------------------- Steuer-ID (11 Ziffern)
def _steuerid_check_digit(first10: str) -> int:
    product = 10
    for ch in first10:
        s = (int(ch) + product) % 10
        if s == 0:
            s = 10
        product = (s * 2) % 11
    check = 11 - product
    return 0 if check == 10 else check


def steuerid_valid(value: str) -> bool:
    """Prüft Aufbau und Prüfziffer einer Steuer-ID nach der öffentlich beschriebenen Regel."""
    s = re.sub(r"\s", "", value)
    if not re.fullmatch(r"\d{11}", s) or s[0] == "0":
        return False
    first10 = s[:10]
    counts = [first10.count(str(d)) for d in range(10)]
    repeated = [c for c in counts if c > 1]
    if len(repeated) != 1 or repeated[0] not in (2, 3):
        return False
    if re.search(r"(\d)\1\1", first10):
        return False
    return int(s[10]) == _steuerid_check_digit(first10)


def make_steuerid(rng: random.Random) -> str:
    while True:
        digits = rng.sample("0123456789", 9)          # 9 verschiedene Ziffern
        digits.insert(rng.randint(0, 9), rng.choice(digits))  # eine davon doppelt -> 10 Stellen
        first10 = "".join(digits)
        if first10[0] != "0" and not re.search(r"(\d)\1\1", first10):
            return first10 + str(_steuerid_check_digit(first10))


def format_steuerid(sid: str, spaced: bool) -> str:
    return f"{sid[:2]} {sid[2:5]} {sid[5:8]} {sid[8:]}" if spaced else sid


# ----------------------------------------------------------------- KVNR (Krankenversichertennummer)
def _kvnr_check_digit(letter: str, eight: str) -> int:
    seq = f"{ord(letter) - 64:02d}" + eight
    total = 0
    for i, ch in enumerate(seq):
        p = int(ch) * (1 if i % 2 == 0 else 2)
        total += p // 10 + p % 10
    return total % 10


def kvnr_valid(value: str) -> bool:
    """Buchstabe + 9 Ziffern, Prüfziffer nach Modulo-10-Verfahren (Annahme nach öffentlicher
    Beschreibung; nicht offiziell verifiziert)."""
    s = value.strip().upper()
    if not re.fullmatch(r"[A-Z]\d{9}", s):
        return False
    return int(s[9]) == _kvnr_check_digit(s[0], s[1:9])


def make_kvnr(rng: random.Random) -> str:
    letter = chr(rng.randint(65, 90))
    eight = "".join(str(rng.randint(0, 9)) for _ in range(8))
    return f"{letter}{eight}{_kvnr_check_digit(letter, eight)}"
