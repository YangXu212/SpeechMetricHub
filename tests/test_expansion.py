import unittest

import numpy as np

from speechmetrichub import run
from speech_eval.phonemes import compare_decoded


class ExpansionTests(unittest.TestCase):
    def test_phone_units_are_not_unicode_characters(self):
        scores, details = compare_decoded("tʃ a", "t a")
        self.assertAlmostEqual(scores["similarity"], 2 / 3)
        self.assertEqual(scores["phone_similarity"], 0.5)
        self.assertEqual(details["reference_phones"], ["tʃ", "a"])

    def test_lps_negative_and_empty(self):
        scores, _ = compare_decoded("a", "b c d")
        self.assertEqual(scores["phone_similarity"], -2)
        with self.assertRaises(ValueError):
            compare_decoded("", "a")

    def test_spectral_gain_semantics(self):
        ref = np.random.default_rng(31).normal(0, 0.1, 16000)
        db = run("lsd_db", reference=ref, hypothesis=ref * 0.5, sample_rate=16000)
        fitted = run("lsd_urgent", reference=ref, hypothesis=ref * 0.5, sample_rate=16000)
        self.assertEqual(db["status"], "ok", db)
        self.assertEqual(fitted["status"], "ok", fitted)
        self.assertAlmostEqual(db["value"], 20 * np.log10(2), places=7)
        self.assertLess(fitted["value"], 1e-5)

    def test_spectral_identity(self):
        ref = np.random.default_rng(32).normal(0, 0.1, 4096)
        for metric in ("lsd_db", "mcd_urgent", "mcd_dtw_c1"):
            with self.subTest(metric=metric):
                result = run(metric, reference=ref, hypothesis=ref, sample_rate=16000)
                self.assertEqual(result["status"], "ok", result)
                self.assertLess(abs(result["value"]), 1e-5)

    def test_spectral_invalid_inputs(self):
        ref = np.ones(2048) * 0.1
        for metric in ("lsd_db", "lsd_urgent", "mcd_urgent", "mcd_dtw_c1"):
            for invalid in (ref[:-1], ref[:, None], ref * 0, ref * np.nan, []):
                result = run(metric, reference=ref, hypothesis=invalid, sample_rate=16000)
                self.assertEqual(result["status"], "invalid_input", result)
                self.assertIsNone(result["value"])

    def test_mcd_profile_metadata(self):
        ref = np.random.default_rng(33).normal(0, 0.1, 4096)
        for metric, start in (("mcd_urgent", 0), ("mcd_dtw_c1", 1)):
            result = run(metric, reference=ref, hypothesis=ref * 0.9, sample_rate=16000)
            self.assertEqual(result["protocol"]["coefficient_start"], start)
            self.assertEqual(result["protocol"]["mcep_order"], 23)
