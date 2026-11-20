"""Kommandozeile des Prüfstands."""
from __future__ import annotations

import argparse
import datetime
import json
import sys

from . import __version__, data, detectors, evaluate, generator, masking, report


def _build_detectors(names: str, plugins: list):
    chosen = []
    for key in [n.strip() for n in names.split(",") if n.strip()]:
        if key not in detectors.BUILTIN:
            sys.exit(f"Unbekannter Detektor '{key}'. Verfügbar: {', '.join(detectors.BUILTIN)}")
        label, fn = detectors.BUILTIN[key]
        chosen.append((key, label, fn))
    for spec in plugins or []:
        label, fn = detectors.load_plugin(spec)
        chosen.append((spec, label, fn))
    if not chosen:
        sys.exit("Kein Detektor gewählt.")
    return chosen


def cmd_run(args):
    docs = generator.generate(args.docs, args.seed)
    chosen = _build_detectors(args.detectors, args.plugin)
    results = []
    for key, label, fn in chosen:
        print(f"→ {label} …", flush=True)
        results.append({"id": key, "name": label, "result": evaluate.evaluate(docs, fn)})
    meta = {"version": __version__, "seed": args.seed, "docs": len(docs),
            "gold_total": results[0]["result"]["gold_total"], "date": datetime.date.today().isoformat()}

    print(f"\n{'Detektor':<44}{'geschützt':>10}{'kritisch':>10}{'FA/100':>8}{'zuordenbar':>12}")
    for r in results:
        x = r["result"]
        print(f"{r['name'][:43]:<44}{x['protected_pct']:>9.1f}%{x['critical_protected_pct']:>9.1f}%"
              f"{x['false_alarms_per_100_docs']:>8.1f}{x['reidentifiable_pct']:>11.1f}%")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump({"meta": meta, "detectors": results}, f, ensure_ascii=False, indent=2)
        print(f"\nJSON: {args.json}")
    if args.html:
        with open(args.html, "w", encoding="utf-8") as f:
            f.write(report.render(meta, results))
        print(f"Bericht: {args.html}")


def cmd_generate(args):
    for d in generator.generate(args.docs, args.seed):
        print(f"--- Dokument {d.id} ({d.kind}) ---")
        print(d.text)
        print("Gold:", [(data.LABEL_DE[s.label], d.text[s.start:s.end]) for s in d.spans], "\n")


def cmd_demo(args):
    doc = generator.generate(1, args.seed)[0]
    print("Original:\n" + doc.text + "\n")
    for key, (label, fn) in detectors.BUILTIN.items():
        masked, mapping = masking.mask(doc.text, fn(doc.text))
        print(f"=== {label} ===\n{masked}\n")
    print("Zurückgesetzt (Referenz) stimmt mit Original überein:",
          masking.restore(*masking.mask(doc.text, detectors.detect_referenz(doc.text))) == doc.text)


def cmd_sample(args):
    docs = generator.generate(args.docs, args.seed)
    out = []
    for d in docs:
        row = d.to_json()
        for key, (label, fn) in detectors.BUILTIN.items():
            row[key] = [[s.start, s.end, s.label] for s in fn(d.text)]
        out.append(row)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"{len(out)} Dokumente -> {args.out}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pruefstand", description="KI-Datenschutz-Prüfstand")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="Detektoren gegeneinander testen")
    r.add_argument("--docs", type=int, default=300)
    r.add_argument("--seed", type=int, default=1)
    r.add_argument("--detectors", default="naiv,referenz", help="Komma-Liste aus: " + ", ".join(detectors.BUILTIN))
    r.add_argument("--plugin", action="append", help="Eigener Detektor: pfad/datei.py:funktion (mehrfach möglich)")
    r.add_argument("--json", help="Ergebnisse als JSON speichern")
    r.add_argument("--html", help="Bericht als HTML speichern")
    r.set_defaults(fn=cmd_run)

    g = sub.add_parser("generate", help="Beispieldokumente mit Gold-Annotationen anzeigen")
    g.add_argument("--docs", type=int, default=2)
    g.add_argument("--seed", type=int, default=1)
    g.set_defaults(fn=cmd_generate)

    d = sub.add_parser("demo", help="Ein Dokument maskieren und zurücksetzen")
    d.add_argument("--seed", type=int, default=3)
    d.set_defaults(fn=cmd_demo)

    s = sub.add_parser("sample", help="Dokumente samt Erkennungen als JSON exportieren (für den Browser-Abgleich)")
    s.add_argument("--docs", type=int, default=40)
    s.add_argument("--seed", type=int, default=7)
    s.add_argument("--out", required=True)
    s.set_defaults(fn=cmd_sample)

    args = ap.parse_args(argv)
    args.fn(args)
