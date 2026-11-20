"""Adapter für Microsoft Presidio (Standardkonfiguration mit deutschem spaCy-Modell).

Installation:
    pip install presidio-analyzer spacy
    python -m spacy download de_core_news_md

Aufruf:
    python -m pruefstand run --plugin examples/presidio_plugin.py:detect --html bericht.html

Konfiguration: Presidio mit den vordefinierten Erkennern und dem Modell de_core_news_md, dazu der
Kreditkarten-Erkenner für Deutsch (in der Grundeinstellung für 'de' nicht aktiv), ohne eigene
deutsche Erkenner für Steuer-ID, Versichertennummer, Adresse oder Gesundheitsdaten. Presidio ist ausdrücklich zum Anpassen gedacht; dieses Ergebnis zeigt
nur die Standardeinstellung. Typen, die der Prüfstand nicht kennt (Orte, Datumsangaben, ...),
zählen als 'OTHER': sie werden bei der Abdeckung mitgezählt, aber nicht beim Typ.
"""
_analyzer = None

MAPPING = {
    "PERSON": "PERSON",
    "EMAIL_ADDRESS": "EMAIL",
    "PHONE_NUMBER": "TELEFON",
    "IBAN_CODE": "IBAN",
    "CREDIT_CARD": "KREDITKARTE",
}


def _get():
    global _analyzer
    if _analyzer is None:
        from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
        from presidio_analyzer.nlp_engine import NlpEngineProvider

        nlp = NlpEngineProvider(nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "de", "model_name": "de_core_news_md"}],
        }).create_engine()
        registry = RecognizerRegistry(supported_languages=["de"])
        registry.load_predefined_recognizers(nlp_engine=nlp, languages=["de"])
        # In dieser Version ist der Kreditkarten-Erkenner für Deutsch nicht aktiv. Das ist eine Frage der
        # Konfiguration und kein Qualitätsurteil, deshalb wird er hier (wie in der Praxis üblich) ergänzt.
        from presidio_analyzer.predefined_recognizers import CreditCardRecognizer
        registry.add_recognizer(CreditCardRecognizer(supported_language="de"))
        _analyzer = AnalyzerEngine(nlp_engine=nlp, registry=registry, supported_languages=["de"])
    return _analyzer


def detect(text):
    results = _get().analyze(text=text, language="de")
    return [(r.start, r.end, MAPPING.get(r.entity_type, "OTHER")) for r in results]
