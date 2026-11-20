"""Tests: python -m unittest discover -s tests -v"""
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pruefstand import detectors, evaluate, generator, masking, validators  # noqa: E402
from pruefstand.core import Span  # noqa: E402


class ValidatorTests(unittest.TestCase):
    def test_known_iban(self):
        self.assertTrue(validators.iban_valid("DE89 3704 0044 0532 0130 00"))
        self.assertFalse(validators.iban_valid("DE89 3704 0044 0532 0130 01"))
        self.assertFalse(validators.iban_valid("DE00"))

    def test_known_card(self):
        self.assertTrue(validators.luhn_valid("4111 1111 1111 1111"))
        self.assertFalse(validators.luhn_valid("4111 1111 1111 1112"))

    def test_generated_values_are_valid(self):
        rng = random.Random(11)
        for _ in range(500):
            self.assertTrue(validators.iban_valid(validators.make_iban(rng)))
            self.assertTrue(validators.luhn_valid(validators.make_card(rng)))
            self.assertTrue(validators.steuerid_valid(validators.make_steuerid(rng)))
            self.assertTrue(validators.kvnr_valid(validators.make_kvnr(rng)))

    def test_steuerid_rejects_broken_values(self):
        sid = validators.make_steuerid(random.Random(3))
        broken = sid[:-1] + str((int(sid[-1]) + 1) % 10)
        self.assertFalse(validators.steuerid_valid(broken))
        self.assertFalse(validators.steuerid_valid("01234567890"))      # beginnt mit 0
        self.assertFalse(validators.steuerid_valid("12345678901"))      # keine doppelte Ziffer


class GeneratorTests(unittest.TestCase):
    def test_deterministic(self):
        a = [d.text for d in generator.generate(25, 4)]
        b = [d.text for d in generator.generate(25, 4)]
        self.assertEqual(a, b)

    def test_spans_point_at_real_text(self):
        for d in generator.generate(100, 2):
            for s in d.spans:
                self.assertTrue(0 <= s.start < s.end <= len(d.text))
                self.assertTrue(d.text[s.start:s.end].strip())


class EvaluateTests(unittest.TestCase):
    def setUp(self):
        self.docs = generator.generate(80, 5)

    def test_oracle_detector_protects_everything(self):
        gold = {d.text: d.spans for d in self.docs}
        res = evaluate.evaluate(self.docs, lambda t: gold[t])
        self.assertEqual(res["protected_pct"], 100.0)
        self.assertEqual(res["false_alarms"], 0)
        self.assertEqual(res["reidentifiable_docs"], 0)

    def test_empty_detector_protects_nothing(self):
        res = evaluate.evaluate(self.docs, lambda t: [])
        self.assertEqual(res["protected_pct"], 0.0)
        self.assertEqual(res["critical_leaked"], res["critical_total"])
        self.assertEqual(res["reidentifiable_pct"], 100.0)

    def test_false_alarm_is_counted(self):
        res = evaluate.evaluate(self.docs, lambda t: [Span(0, 3, "PERSON")])
        self.assertGreater(res["false_alarms"], 0)

    def test_reference_beats_naive_on_finance_and_health(self):
        docs = generator.generate(200, 1)
        naiv = evaluate.evaluate(docs, detectors.detect_naiv)
        ref = evaluate.evaluate(docs, detectors.detect_referenz)
        self.assertGreater(ref["protected_pct"], naiv["protected_pct"] + 40)
        self.assertEqual(ref["per_label"]["IBAN"]["protected_pct"], 100.0)
        self.assertEqual(ref["per_label"]["KVNR"]["protected_pct"], 100.0)


class MaskingTests(unittest.TestCase):
    def test_roundtrip_exact(self):
        for d in generator.generate(150, 9):
            masked, mapping = masking.mask(d.text, detectors.detect_referenz(d.text))
            self.assertEqual(masking.restore(masked, mapping), d.text)

    def test_same_value_same_placeholder(self):
        text = "Anna Müller schrieb. Später antwortete Anna Müller."
        second = text.index("Anna", 1)
        spans = [Span(0, 11, "PERSON"), Span(second, second + 11, "PERSON")]
        masked, mapping = masking.mask(text, spans)
        self.assertEqual(masked.count("[PERSON_1]"), 2)
        self.assertEqual(len(mapping), 1)

    def test_restore_survives_model_rewording(self):
        masked, mapping = masking.mask("IBAN DE89 3704 0044 0532 0130 00 prüfen", [Span(5, 32, "IBAN")])
        answer = "Die Angabe [IBAN_1] ist gültig."
        self.assertEqual(masking.restore(answer, mapping), "Die Angabe DE89 3704 0044 0532 0130 00 ist gültig.")


class PluginTests(unittest.TestCase):
    def test_plugin_loading(self):
        path = os.path.join(os.path.dirname(__file__), "..", "examples", "eigener_filter.py")
        name, fn = detectors.load_plugin(path + ":detect")
        text = "Mail an test@example.org bitte"
        out = fn(text)
        self.assertEqual([(s.label, text[s.start:s.end]) for s in out], [("EMAIL", "test@example.org")])

    def test_plugin_spec_without_function_name(self):
        path = os.path.join(os.path.dirname(__file__), "..", "examples", "eigener_filter.py")
        name, fn = detectors.load_plugin(path)          # ohne ':detect' -> Standardname
        self.assertTrue(callable(fn))


if __name__ == "__main__":
    unittest.main()
