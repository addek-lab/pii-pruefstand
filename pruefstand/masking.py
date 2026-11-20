"""Umkehrbares Maskieren: sensible Angaben durch Platzhalter ersetzen und später zurücksetzen."""
from __future__ import annotations

import re


def mask(text: str, spans):
    """Gibt (maskierter Text, Zuordnung) zurück. Gleiche Werte bekommen denselben Platzhalter.
    Die Spans dürfen sich nicht überlappen (siehe detectors.resolve)."""
    mapping, reverse, counters = {}, {}, {}
    out, pos = [], 0
    for s in sorted(spans, key=lambda x: x.start):
        if s.start < pos:
            continue
        value = text[s.start:s.end]
        key = (s.label, value)
        if key not in reverse:
            counters[s.label] = counters.get(s.label, 0) + 1
            ph = f"[{s.label}_{counters[s.label]}]"
            reverse[key] = ph
            mapping[ph] = value
        out.append(text[pos:s.start])
        out.append(reverse[key])
        pos = s.end
    out.append(text[pos:])
    return "".join(out), mapping


def restore(text: str, mapping: dict) -> str:
    """Setzt Platzhalter in einem (z. B. von einer KI erzeugten) Text wieder auf die Originale."""
    if not mapping:
        return text
    pattern = re.compile("|".join(re.escape(k) for k in sorted(mapping, key=len, reverse=True)))
    return pattern.sub(lambda m: mapping[m.group(0)], text)
