"""Semantic tests for voicing masks, units, boundary cases and actual backends."""

import importlib.util
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

from speech_eval.pitch import _counts, _select, evaluate_pitch, pitch_metric
from speechmetrichub import evaluate, evaluate_batch


class PitchStatisticsTests(unittest.TestCase):
    def test_confusion_and_common_voiced_rmse(self):
        # TP=2, FP=1, FN=1, TN=1; matched voiced errors are 10 and -20 Hz.
        data = _counts([100, 0, 200, 0, 150], [110, 50, 0, 0, 130])
        self.assertEqual([data[k] for k in ("TP", "FP", "FN", "TN")], [2, 1, 1, 1])
        self.assertEqual(data["squared_error_sum"], 500)
        self.assertEqual(data["scored_frames"], 2)
        self.assertEqual(data["common_voiced_fraction"], 0.4)
        common = {"details": data, "protocol": {}}
        self.assertAlmostEqual(_select("vuv_f1", common)["value"], 2 / 3)
        self.assertAlmostEqual(_select("f0_rmse", common)["value"], np.sqrt(250))

    def test_octave_error_is_not_voicing_error(self):
        data = _counts([100, 100, 0], [200, 200, 0])
        common = {"details": data, "protocol": {}}
        self.assertEqual(_select("vuv_f1", common)["value"], 1)
        self.assertEqual(_select("f0_rmse", common)["value"], 100)
        logdata = _counts([100, 100, 0], [200, 200, 0], logarithmic=True)
        self.assertAlmostEqual(
            _select("log_f0_rmse_espnet", {"details": logdata, "protocol": {}})["value"],
            np.log(2),
        )

    def test_unvoiced_support_is_not_a_perfect_result(self):
        for a, b in (([0, 0], [0, 0]), ([100, 0], [0, 100])):
            common = {"details": _counts(a, b), "protocol": {}}
            self.assertIsNone(_select("f0_rmse", common)["value"])
        common = {"details": _counts([0, 0], [0, 0]), "protocol": {}}
        self.assertEqual(_select("vuv_f1", common)["status"], "undefined_result")
        for a, b in (([100, 100], [0, 0]), ([0, 0], [100, 100])):
            common = {"details": _counts(a, b), "protocol": {}}
            self.assertEqual(_select("vuv_f1", common)["value"], 0)
            self.assertEqual(_select("vuv_f1", common)["status"], "ok")

    def test_amphion_all_frame_mask_differs(self):
        a, b = [100, 0], [100, 100]
        joint, all_frames = _counts(a, b), _counts(a, b, common_only=False)
        self.assertEqual(joint["squared_error_sum"], 0)
        self.assertEqual(all_frames["squared_error_sum"], 10000)
        self.assertEqual(all_frames["scored_frames"], 2)

    def test_contour_validation(self):
        for a, b in (([], []), ([1], [1, 2]), ([-1], [1]), ([np.nan], [1])):
            with self.assertRaises(ValueError):
                _counts(a, b)

    def test_evaluate_shares_extraction(self):
        common = {"details": _counts([100], [100]), "protocol": {}}
        with patch("speech_eval.pitch._prepare", return_value=common) as prepare:
            results = evaluate_pitch(["vuv_f1", "f0_rmse"], reference="r", hypothesis="h")
        self.assertEqual(prepare.call_count, 1)
        self.assertEqual(results["vuv_f1"]["value"], 1)
        self.assertEqual(results["f0_rmse"]["value"], 0)

    def test_public_batch_pools_f1_counts_and_preserves_failures(self):
        one = {"details": _counts([100], [100]), "protocol": {}}
        nine = {"details": _counts([100] * 9, [0] * 9), "protocol": {}}
        records = [
            {"id": str(i), "inputs": {"reference": "r", "hypothesis": "h"}} for i in range(3)
        ]
        failure = {"status": "invalid_input", "value": None, "reason": "invalid fixture"}
        with patch("speech_eval.pitch._prepare", side_effect=[one, nine]):
            batch = evaluate_batch("vuv_f1", records[:2])
        self.assertTrue(batch["complete"])
        self.assertAlmostEqual(batch["value"], 2 / 11)
        self.assertNotAlmostEqual(batch["value"], 0.5)
        self.assertEqual(batch["counts"]["FN"], 9)
        with patch("speech_eval.pitch._prepare", side_effect=[one, nine, failure]):
            partial = evaluate_batch("vuv_f1", records)
        self.assertFalse(partial["complete"])
        self.assertIsNone(partial["value"])
        self.assertAlmostEqual(partial["valid_subset_value"], 2 / 11)
        self.assertEqual(len(partial["rows"]), 3)
        self.assertEqual(partial["rows"][2]["result"]["status"], "invalid_input")

    def test_public_batch_rmse_pools_squared_error_and_support(self):
        one = {"details": _counts([100], [200]), "protocol": {}}
        nine = {"details": _counts([100] * 9, [100] * 9), "protocol": {}}
        records = [
            {"id": str(i), "inputs": {"reference": "r", "hypothesis": "h"}} for i in range(2)
        ]
        with patch("speech_eval.pitch._prepare", side_effect=[one, nine]):
            batch = evaluate_batch("f0_rmse", records)
        self.assertTrue(batch["complete"])
        self.assertAlmostEqual(batch["value"], np.sqrt(1000))
        self.assertNotAlmostEqual(batch["value"], 50)
        self.assertEqual(batch["counts"]["scored_frames"], 10)


@unittest.skipUnless(importlib.util.find_spec("pyworld"), "pyworld optional dependency")
class WorldPitchTests(unittest.TestCase):
    @staticmethod
    def voiced():
        # Rich periodic waveform: pure sine waves can be UV under Harvest.
        time = np.arange(16000) / 16000
        return sum(np.sin(2 * np.pi * 160 * k * time) / k for k in range(1, 15)) * 0.1

    def test_actual_harvest_identity_and_silence(self):
        wave = self.voiced()
        scores = evaluate_pitch(
            ["vuv_f1", "f0_rmse"], reference=wave, hypothesis=wave, sample_rate=16000
        )
        self.assertEqual(scores["vuv_f1"]["status"], "ok", scores)
        self.assertEqual(scores["vuv_f1"]["value"], 1)
        self.assertEqual(scores["f0_rmse"]["value"], 0)
        self.assertGreater(scores["f0_rmse"]["details"]["scored_frames"], 100)
        silent = pitch_metric(
            metric="vuv_f1", reference=wave, hypothesis=np.zeros_like(wave), sample_rate=16000
        )
        self.assertEqual(silent["status"], "ok", silent)
        self.assertEqual(silent["value"], 0)

    def test_public_evaluate_extracts_once_per_waveform(self):
        import pyworld

        wave = self.voiced()
        with patch("pyworld.harvest", wraps=pyworld.harvest) as harvest:
            scores = evaluate(
                ["vuv_f1", "f0_rmse"], reference=wave, hypothesis=wave, sample_rate=16000
            )
        self.assertEqual(harvest.call_count, 2)
        self.assertEqual(scores["vuv_f1"]["value"], 1)
        self.assertEqual(scores["f0_rmse"]["value"], 0)

    def test_no_hidden_crop_resample_or_invalid_params(self):
        wave = self.voiced()
        cases = [
            dict(hypothesis=wave[:-1]),
            dict(hypothesis=wave[:, None]),
            dict(hypothesis=wave, frame_period=0),
            dict(hypothesis=wave, sample_rate=8000),
            dict(hypothesis=wave, f0_min=1000, f0_max=800),
            dict(hypothesis=wave, method="dtw"),
            dict(hypothesis=np.array([np.nan] * len(wave))),
        ]
        for inputs in cases:
            args = {"reference": wave, "sample_rate": 16000, **inputs}
            result = pitch_metric(metric="f0_rmse", **args)
            self.assertEqual(result["status"], "invalid_input", (inputs.keys(), result))

    def test_native_file_rate_inference_and_mismatch(self):
        import soundfile as sf

        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / "a.wav", Path(folder) / "b.wav"
            wave = self.voiced()
            sf.write(a, wave, 16000)
            sf.write(b, wave, 24000)
            good = pitch_metric(metric="vuv_f1", reference=a, hypothesis=a)
            self.assertEqual(good["value"], 1)
            self.assertEqual(good["protocol"]["sample_rate"], 16000)
            bad = pitch_metric(metric="vuv_f1", reference=a, hypothesis=b)
            self.assertEqual(bad["status"], "invalid_input")
            # FLOAT WAV NaN/Inf must not be concealed by ESPnet int16 decoding.
            for value in (np.nan, np.inf):
                corrupt = wave.copy()
                corrupt[100] = value
                sf.write(b, corrupt, 16000, subtype="FLOAT")
                for metric in ("vuv_f1", "log_f0_rmse_espnet"):
                    bad = pitch_metric(metric=metric, reference=a, hypothesis=b)
                    self.assertEqual(bad["status"], "invalid_input", bad)


if __name__ == "__main__":
    unittest.main()
