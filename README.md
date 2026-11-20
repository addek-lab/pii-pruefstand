# KI-Datenschutz-Prüfstand

Ein offenes Testwerkzeug, das misst, **wie gut Datenschutzfilter deutsche Finanz- und Gesundheitsdaten schützen**, bevor ein Text in eine KI geht.

Viele Werkzeuge versprechen, „personenbezogene Daten zu filtern“. Dieses Projekt macht daraus eine Zahl: Es erzeugt synthetische deutsche Dokumente mit exakten Lösungen, lässt Filter dagegen antreten und zeigt, **was sichtbar bleibt**.

- Läuft mit reinem Python 3, **ohne Zusatzpakete**
- Synthetische Daten, nie echte Personen
- Reproduzierbar: gleicher Seed, gleiche Zahlen
- Eigene Filter lassen sich in wenigen Zeilen einhängen
- Live-Demo im Browser: siehe die Webseite zum Projekt

## Ergebnisse (300 Dokumente, 1.822 sensible Angaben, Seed 1)

| Verfahren | geschützt | kritische Angaben durchgerutscht | Falschalarme / 100 Dokumente |
|---|---|---|---|
| Einfacher Regex-Filter | 16,8 % | 624 von 737 | 4,3 |
| Presidio 2.2 (Standard + dt. Modell) | 61,9 % | 409 von 737 | 135,7 |
| Referenz-Regeln (Prüfsumme + Kontext) | 87,3 % | 80 von 737 | 9,7 |

Nach Bereich (geschützt): Finanzdaten 33,4 % / 76,3 % / 100 %, Gesundheitsdaten 0 % / 17,0 % / 82,6 %, Identität 18,9 % / 77,3 % / 85,3 % (gleiche Reihenfolge der Verfahren).

**Bitte fair lesen:** Presidio ist ein Baukasten zum Anpassen. Getestet wurde die Standardkonfiguration mit `de_core_news_md` plus nachträglich aktiviertem Kreditkarten-Erkenner (in der Grundeinstellung für Deutsch nicht aktiv). Für Steuer-ID, Versichertennummer, Adressen und Gesundheitsdaten gibt es dort keine deutschen Erkenner. Die Falschalarme entstehen, weil das Sprachmodell Termine, Anreden und Großgeschriebenes als Personen, Orte oder Daten meldet. Das ist **kein Urteil über das Produkt**. Die Namenserkennung ist besser als die der Referenz-Regeln (94,6 % gegenüber 78,3 %).

Den vollständigen Bericht findest du in `results/bericht.html`, die Rohdaten in `results/ergebnisse.json`.

## Schnellstart

```bash
python -m pruefstand run --html bericht.html      # Test mit den eingebauten Verfahren
python -m pruefstand demo                         # ein Dokument maskieren und zurücksetzen
python -m pruefstand generate --docs 3            # Beispieldokumente mit Lösung ansehen
python -m unittest discover -s tests              # Tests
```

Alle Optionen: `python -m pruefstand run --help` (Anzahl Dokumente, Seed, JSON-Ausgabe, Plugins).

## Eigenen Filter testen

```python
# mein_filter.py
import re

def detect(text):
    # (start, ende, typ) je gefundener Stelle
    return [(m.start(), m.end(), "EMAIL") for m in re.finditer(r"[\w.+-]+@[\w.-]+", text)]
```

```bash
python -m pruefstand run --plugin mein_filter.py:detect --html bericht.html
```

Bekannte Typen: `PERSON, ADRESSE, PLZ_ORT, GEBURTSDATUM, TELEFON, EMAIL, IBAN, BIC, KREDITKARTE, STEUER_ID, KVNR, ICD10, DIAGNOSE, MEDIKAMENT`. Alles andere zählt als `OTHER` (bei der Abdeckung mitgezählt, nicht beim Typ).

Ein Adapter für Microsoft Presidio liegt in `examples/presidio_plugin.py` (Installation steht in der Datei).

## Was gemessen wird

- **Geschützt:** Mindestens 80 % der Zeichen einer sensiblen Angabe werden von irgendeiner Erkennung überdeckt, egal mit welchem Typ. Beim Maskieren zählt, dass es verschwindet.
- **Kritisch:** IBAN, Kreditkarte, Steuer-ID, Krankenversichertennummer, ICD-10-Code, Diagnose, Medikament.
- **Falschalarm:** Eine Erkennung, die keine sensible Angabe überdeckt (z. B. Termin, Auftragsnummer, Hotline, „Herr Kundenberater“).
- **Zuordenbar:** Ein Dokument gilt als weiter einer Person zuordenbar, wenn ein Name oder die Kombination aus Geburtsdatum und Wohnort/Adresse sichtbar bleibt. Das ist eine einfache Heuristik, kein Re-Identifikationsmodell.
- **Umkehrbares Maskieren** (`pruefstand/masking.py`): Platzhalter wie `[IBAN_1]`, gleiche Werte bekommen denselben Platzhalter, und der Text lässt sich nach der Antwort einer KI exakt zurücksetzen. Das ist getestet.

## Daten

Der Generator (`pruefstand/generator.py`) erzeugt sieben Dokumenttypen: Arztbrief, Überweisung, Kreditantrag, Support-Ticket, Kostenübernahme, Kontoauszug, Beschwerde. Alle Personen, Nummern und Adressen sind erfunden. IBAN, Kreditkarte, Steuer-ID und KVNR haben gültige Prüfziffern. Zufällige Übereinstimmungen mit echten Nummern sind nicht ausgeschlossen, aber extrem unwahrscheinlich.

## Grenzen (bitte lesen)

- **Synthetische Daten sind sauberer als echte.** Die Zahlen zeigen Muster und Größenordnungen, **keine Gütesiegel**.
- **Die Referenz-Regeln stammen vom Autor** und kennen die Formate des Generators. Sie sind eher eine Obergrenze für regelbasierte Erkennung als ein Abbild der Praxis. Wortlisten für Namen, Medikamente und Diagnosen sind bewusst nur teilweise bekannt.
- Die **KVNR-Prüfziffer** folgt meinem Verständnis der öffentlichen Beschreibung und ist nicht offiziell verifiziert.
- Nur deutsche Texte, nur die genannten Dokumenttypen, nur Textformate (keine Bilder, PDFs, Tabellen).
- **Keine Rechtsberatung, keine Zertifizierung.** Pseudonymisierte Daten bleiben nach der DSGVO oft personenbezogen. Ob ein Verfahren für einen konkreten Einsatz reicht, klären Datenschutzbeauftragte oder Juristen.

## Ideen für die Weiterentwicklung

Weitere Dokumenttypen und Sprachen, weitere Verfahren (z. B. lokale Sprachmodelle als Erkenner), ein besseres Maß für Re-Identifizierbarkeit, Abdeckung von Tabellen und PDFs, automatische Läufe in CI. Beiträge sind willkommen.

## Lizenz

MIT, siehe `LICENSE`. Der Adapter für Presidio nutzt dessen Paket `presidio-analyzer` (MIT-Lizenz) und das spaCy-Modell `de_core_news_md`.
