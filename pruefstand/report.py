"""Erzeugt einen eigenständigen HTML-Bericht (ein File, ohne externe Abhängigkeiten)."""
from __future__ import annotations

import html

from . import data
from .evaluate import DOMAINS

CSS = """
:root{--bg:#f8fafc;--panel:#fff;--line:#e2e8f0;--ink:#0f172a;--mut:#475569;--cy:#0e7490;--ok:#047857;--bad:#be123c;--warn:#b45309;--bar:#e2e8f0}
@media (prefers-color-scheme:dark){:root{--bg:#090D16;--panel:#0f172a;--line:#1E293B;--ink:#f1f5f9;--mut:#94a3b8;--cy:#22d3ee;--ok:#34d399;--bad:#fb7185;--warn:#fbbf24;--bar:#1E293B}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,-apple-system,Segoe UI,Inter,sans-serif}
main{max-width:1040px;margin:0 auto;padding:40px 20px 80px}h1{font-size:2rem;margin:.2em 0}h2{margin:2.2em 0 .6em;font-size:1.35rem}
.mut{color:var(--mut)}.tag{font:600 .75rem ui-monospace,Consolas,monospace;color:var(--cy);letter-spacing:.08em}
.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:20px}
.big{font-size:2.6rem;font-weight:800;line-height:1.1}.ok{color:var(--ok)}.bad{color:var(--bad)}.warn{color:var(--warn)}
.row{display:grid;grid-template-columns:150px 1fr 56px;gap:10px;align-items:center;margin:6px 0;font-size:.9rem}
.bar{background:var(--bar);border-radius:99px;height:12px;overflow:hidden}.bar>i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,#06B6D4,#6366F1)}
table{width:100%;border-collapse:collapse;font-size:.9rem}th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--mut);font-weight:600}code{font:.85em ui-monospace,Consolas,monospace;background:var(--bar);padding:1px 5px;border-radius:5px}
.note{border-left:3px solid var(--warn);padding:.2em 1em;color:var(--mut)}
"""


def _pct(v):
    return "–" if v is None else f"{v:.1f} %".replace(".", ",")


def _cls(v, good=90, mid=60):
    if v is None:
        return ""
    return "ok" if v >= good else ("warn" if v >= mid else "bad")


def render(meta: dict, detectors: list) -> str:
    e = html.escape
    out = [f"<!doctype html><html lang='de'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
           f"<title>KI-Datenschutz-Prüfstand: Bericht</title><style>{CSS}</style></head><body><main>"]
    out.append("<p class='tag'>KI-DATENSCHUTZ-PRÜFSTAND · BERICHT</p><h1>Wie gut schützen Filter deutsche Finanz- und Gesundheitsdaten?</h1>")
    out.append(f"<p class='mut'>{meta['docs']} synthetische Dokumente · {meta['gold_total']} sensible Angaben · Seed {meta['seed']} · "
               f"Version {e(meta['version'])} · {e(meta['date'])}. Alle Daten sind erfunden. Siehe Methodik am Ende.</p>")

    out.append("<h2>Ergebnis auf einen Blick</h2><div class='grid'>")
    for d in detectors:
        r = d["result"]
        out.append(f"<div class='card'><div class='tag'>{e(d['name'])}</div>"
                   f"<div class='big {_cls(r['protected_pct'])}'>{_pct(r['protected_pct'])}</div>"
                   f"<div class='mut'>der sensiblen Angaben geschützt</div><hr style='border:0;border-top:1px solid var(--line);margin:14px 0'>"
                   f"<div><b>{r['critical_leaked']}</b> von {r['critical_total']} kritischen Angaben durchgerutscht "
                   f"(IBAN, Kreditkarte, Steuer-ID, KVNR, Diagnose, Medikament)</div>"
                   f"<div><b>{_pct(r['reidentifiable_pct'])}</b> der Dokumente weiterhin einer Person zuordenbar</div>"
                   f"<div><b>{str(r['false_alarms_per_100_docs']).replace('.', ',')}</b> Falschalarme je 100 Dokumente</div></div>")
    out.append("</div>")

    out.append("<h2>Nach Bereich</h2><div class='card'>")
    for dom in DOMAINS:
        out.append(f"<h3 style='margin:.6em 0 .2em'>{dom}</h3>")
        for d in detectors:
            v = d["result"]["domains"][dom]["protected_pct"]
            out.append(f"<div class='row'><span>{e(d['name'])}</span><div class='bar'><i style='width:{v or 0}%'></i></div><b>{_pct(v)}</b></div>")
    out.append("</div>")

    out.append("<h2>Nach Art der Angabe</h2><div class='card'><table><tr><th>Angabe</th>"
               + "".join(f"<th>{e(d['name'])}</th>" for d in detectors) + "<th>Anzahl</th></tr>")
    for lab in data.ALL_LABELS:
        n = detectors[0]["result"]["per_label"][lab]["n"]
        cells = "".join(f"<td class='{_cls(d['result']['per_label'][lab]['protected_pct'])}'>{_pct(d['result']['per_label'][lab]['protected_pct'])}</td>"
                        for d in detectors)
        crit = " ⚠" if lab in data.CRITICAL else ""
        out.append(f"<tr><td>{e(data.LABEL_DE[lab])}{crit}</td>{cells}<td>{n}</td></tr>")
    out.append("</table><p class='mut'>⚠ = als kritisch eingestuft (Finanz- und Gesundheitsdaten). Geschützt = mindestens 80 % der Zeichen überdeckt.</p></div>")

    out.append("<h2>Was durchrutscht (Beispiele)</h2>")
    for d in detectors:
        misses = d["result"]["misses"]
        if not misses:
            continue
        out.append(f"<div class='card' style='margin-bottom:16px'><div class='tag'>{e(d['name'])}</div><table><tr><th>Art</th><th>Nicht erkannt</th><th>Umgebung</th></tr>")
        shown = 0
        for lab in data.ALL_LABELS:
            for m in misses.get(lab, [])[:1]:
                out.append(f"<tr><td>{e(data.LABEL_DE[lab])}</td><td><code>{e(m['text'])}</code></td><td class='mut'>…{e(m['context'])}…</td></tr>")
                shown += 1
        out.append("</table></div>")

    if any(d.get("id") == "presidio" for d in detectors):
        out.append("<h2>Hinweis zu Presidio</h2><div class='note'><p>Microsoft Presidio ist ein Baukasten, der für eigene Anpassungen "
                   "gedacht ist. Getestet wurde die Standardkonfiguration mit dem deutschen spaCy-Modell <code>de_core_news_md</code>, dazu der "
                   "nachträglich aktivierte Kreditkarten-Erkenner (in der Grundeinstellung für Deutsch nicht aktiv). Für Steuer-ID, "
                   "Versichertennummer, Adressen und Gesundheitsdaten bringt Presidio keine deutschen Erkenner mit. Die Falschalarme entstehen, weil "
                   "das Sprachmodell Termine, Anreden und Großgeschriebenes als Personen, Orte oder Daten meldet; jede Erkennung ohne sensible "
                   "Angabe zählt als Falschalarm. <b>Das ist kein Urteil über das Produkt</b>, sondern der Ausgangspunkt ohne eigene Anpassung.</p></div>")

    out.append("""<h2>Methodik und Grenzen</h2><div class='card'>
<ul>
<li><b>Daten:</b> Ein Generator erzeugt deutschsprachige Dokumente (Arztbrief, Überweisung, Kreditantrag, Support-Ticket, Kostenübernahme, Kontoauszug, Beschwerde) mit exakten Annotationen. Alle Personen, Nummern und Adressen sind erfunden. IBAN, Kreditkarte, Steuer-ID und KVNR haben gültige Prüfziffern.</li>
<li><b>Störgrößen:</b> Die Dokumente enthalten absichtlich Dinge, die nach Personendaten aussehen, aber keine sind (Termine, Auftragsnummern, Hotlines, Artikelnummern), um Falschalarme zu messen.</li>
<li><b>Geschützt</b> heißt: mindestens 80 % der Zeichen einer sensiblen Angabe werden von irgendeiner Erkennung überdeckt, egal mit welchem Typ. Beim Maskieren zählt, dass es verschwindet.</li>
<li><b>Zuordenbar</b> ist ein Dokument, wenn ein Name oder die Kombination Geburtsdatum + Wohnort/Adresse sichtbar bleibt. Das ist eine einfache Heuristik, kein Re-Identifikationsmodell.</li>
<li><b>Grenzen:</b> Synthetische Daten sind sauberer als echte. Die Referenz-Regeln stammen vom Autor und kennen die Formate des Generators; sie sind eher eine Obergrenze für regelbasierte Erkennung. Die Wortlisten für Namen, Medikamente und Diagnosen sind bewusst nur teilweise bekannt. Die KVNR-Prüfziffer folgt meinem Verständnis der öffentlichen Beschreibung. Der Bericht ist <b>keine Rechtsberatung</b> und keine Zertifizierung.</li>
<li><b>Reproduzierbar:</b> Gleicher Seed, gleiche Dokumente, gleiche Zahlen.</li>
</ul></div></main></body></html>""")
    return "".join(out)
