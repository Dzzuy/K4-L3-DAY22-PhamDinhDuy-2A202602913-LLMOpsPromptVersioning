"""Regression checks for the two custom output validators."""

import importlib.util
import json
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "src" / "04_guardrails_validator.py"
SPEC = importlib.util.spec_from_file_location("guardrails_lab", SOURCE)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def make_guard(validator):
    guard = MODULE.Guard()
    guard.configure(allow_metrics_collection=False)
    return guard.use(validator(on_fail=MODULE.OnFailAction.FIX))


class PIIDetectorTests(unittest.TestCase):
    def test_redacts_all_supported_types_and_preserves_clean_text(self):
        guard = make_guard(MODULE.PIIDetector)
        cases = {
            "email": ("a@example.com", "[EMAIL_REDACTED]"),
            "phone": ("(555) 867-5309", "[PHONE_REDACTED]"),
            "ssn": ("123-45-6789", "[SSN_REDACTED]"),
            "card": ("4532 1234 5678 9010", "[CREDIT_CARD_REDACTED]"),
        }
        for label, (raw, expected) in cases.items():
            with self.subTest(label=label):
                output = guard.validate(f"Value: {raw}").validated_output
                self.assertIn(expected, output)
                self.assertNotIn(raw, output)
        clean = "No sensitive information in this text."
        self.assertEqual(guard.validate(clean).validated_output, clean)


class JSONFormatterTests(unittest.TestCase):
    def test_repair_and_fallback_are_parseable(self):
        guard = make_guard(MODULE.JSONFormatter)
        cases = [
            ('{"ok": true}', {"ok": True}),
            ('```json\n{"ok": true}\n```', {"ok": True}),
            ("{'ok': true}", {"ok": True}),
            ('{"ok": true,}', {"ok": True}),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(json.loads(guard.validate(raw).validated_output), expected)
        fallback = json.loads(guard.validate("not json {]").validated_output)
        self.assertIn("error", fallback)
        self.assertEqual(fallback["raw"], "not json {]")


if __name__ == "__main__":
    unittest.main()
