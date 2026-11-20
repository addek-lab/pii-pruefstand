"""Auswertung: Wie viel Sensibles bleibt sichtbar?

Hauptmaß ist die ABDECKUNG: Eine sensible Angabe gilt als geschützt, wenn mindestens 80 % ihrer
Zeichen von irgendeiner Erkennung überdeckt werden (egal mit welchem Typ). Denn beim Maskieren
zählt, dass es verschwindet, nicht, wie es heißt. Der Typ wird zusätzlich ausgewertet.
"""
from __future__ import annotations

import time

from . import data
from .core import Doc, Span

DOMAINS = {
    "Finanzdaten": ["IBAN", "BIC", "KREDITKARTE", "STEUER_ID"],
    "Gesundheitsdaten": ["KVNR", "ICD10", "DIAGNOSE", "MEDIKAMENT"],
    "Identität": ["PERSON", "GEBURTSDATUM", "ADRESSE", "PLZ_ORT", "TELEFON", "EMAIL"],
}
LABEL_DOMAIN = {lab: dom for dom, labs in DOMAINS.items() for lab in labs}


def coverage(gold: Span, dets) -> float:
    ivs = sorted((max(d.start, gold.start), min(d.end, gold.end))
                 for d in dets if d.end > gold.start and d.start < gold.end)
    covered, cur = 0, gold.start
    for s, e in ivs:
        s = max(s, cur)
        if e > s:
            covered += e - s
            cur = e
    return covered / gold.length()


def _iou(a: Span, b: Span) -> float:
    inter = max(0, min(a.end, b.end) - max(a.start, b.start))
    union = a.length() + b.length() - inter
    return inter / union if union else 0.0


def _overlaps_any(d: Span, golds) -> bool:
    return any(d.end > g.start and d.start < g.end for g in golds)


def _flag_reidentifiable(uncovered_labels: set) -> bool:
    return ("PERSON" in uncovered_labels
            or {"GEBURTSDATUM", "PLZ_ORT"} <= uncovered_labels
            or {"GEBURTSDATUM", "ADRESSE"} <= uncovered_labels)


def evaluate(docs: list, detect, max_examples: int = 4) -> dict:
    per = {lab: {"n": 0, "covered": 0, "typed_tp": 0} for lab in data.ALL_LABELS}
    fp = fp_chars = det_total = 0
    reid = 0
    misses = {}
    t0 = time.perf_counter()
    for doc in docs:
        dets = detect(doc.text)
        det_total += len(dets)
        uncovered = set()
        for g in doc.spans:
            p = per[g.label]
            p["n"] += 1
            cov = coverage(g, dets)
            if cov >= 0.8:
                p["covered"] += 1
            else:
                uncovered.add(g.label)
                lst = misses.setdefault(g.label, [])
                if len(lst) < max_examples:
                    a, b = max(0, g.start - 24), min(len(doc.text), g.end + 24)
                    lst.append({"doc": doc.id, "text": doc.text[g.start:g.end],
                                "context": doc.text[a:b].replace("\n", " ⏎ "), "coverage": round(cov, 2)})
            if any(d.label == g.label and _iou(g, d) >= 0.5 for d in dets):
                p["typed_tp"] += 1
        for d in dets:
            if not _overlaps_any(d, doc.spans):
                fp += 1
                fp_chars += d.length()
        if _flag_reidentifiable(uncovered):
            reid += 1
    ms_per_doc = (time.perf_counter() - t0) / max(1, len(docs)) * 1000

    n_all = sum(p["n"] for p in per.values())
    cov_all = sum(p["covered"] for p in per.values())
    crit = [lab for lab in data.CRITICAL]
    n_crit = sum(per[l]["n"] for l in crit)
    cov_crit = sum(per[l]["covered"] for l in crit)
    typed = sum(p["typed_tp"] for p in per.values())
    precision = typed / det_total if det_total else 0.0
    recall_typed = typed / n_all if n_all else 0.0

    domains = {}
    for dom, labs in DOMAINS.items():
        n = sum(per[l]["n"] for l in labs)
        c = sum(per[l]["covered"] for l in labs)
        domains[dom] = {"n": n, "covered": c, "protected_pct": round(100 * c / n, 1) if n else None}

    return {
        "docs": len(docs),
        "gold_total": n_all,
        "protected_pct": round(100 * cov_all / n_all, 1) if n_all else 0.0,
        "leaked": n_all - cov_all,
        "critical_total": n_crit,
        "critical_leaked": n_crit - cov_crit,
        "critical_protected_pct": round(100 * cov_crit / n_crit, 1) if n_crit else 0.0,
        "false_alarms": fp,
        "false_alarms_per_100_docs": round(100 * fp / max(1, len(docs)), 1),
        "reidentifiable_docs": reid,
        "reidentifiable_pct": round(100 * reid / max(1, len(docs)), 1),
        "typed_precision": round(100 * precision, 1),
        "typed_recall": round(100 * recall_typed, 1),
        "ms_per_doc": round(ms_per_doc, 2),
        "per_label": {lab: {**v, "protected_pct": round(100 * v["covered"] / v["n"], 1) if v["n"] else None}
                      for lab, v in per.items()},
        "domains": domains,
        "misses": misses,
    }
