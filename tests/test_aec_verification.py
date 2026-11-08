import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from speechmetrichub import run, evaluate_batch, create_deployment, verify_deployment


class VerificationTests(unittest.TestCase):
    def test_eer_known_operating_points(self):
        for scores, expected in (([0, 1], 0), ([1, 0], 100), ([1, 1], 50)):
            result = run("eer", scores=scores, labels=[0, 1])
            self.assertEqual(result["value"], expected, result)
        tied = run("eer", scores=[1, 1], labels=[0, 1])
        self.assertTrue(tied["details"]["interpolated"])
        self.assertIsNone(tied["details"]["threshold"])

    def test_score_direction_and_tie_order(self):
        a = run("eer", scores=[0, 0, 1, 2], labels=[0, 1, 1, 0])
        b = run(
            "eer", scores=[0, 0, -1, -2], labels=[1, 0, 1, 0], score_direction="lower_is_target"
        )
        self.assertEqual(a["value"], b["value"])

    def test_min_dcf_matches_exhaustive_thresholds(self):
        rng = np.random.default_rng(51)
        for _ in range(100):
            scores = rng.integers(-3, 4, 40)
            labels = np.r_[np.ones(20), np.zeros(20)]
            prior = float(rng.uniform(0.001, 0.999))
            miss, fa = float(rng.uniform(0.1, 4)), float(rng.uniform(0.1, 4))
            costs = []
            for threshold in [np.inf, *sorted(set(scores), reverse=True)]:
                accepted = scores >= threshold
                pm = np.mean(~accepted[labels == 1])
                pf = np.mean(accepted[labels == 0])
                costs.append(miss * prior * pm + fa * (1 - prior) * pf)
            for normalized in (True, False):
                result = run(
                    "min_dcf",
                    scores=scores,
                    labels=labels,
                    p_target=prior,
                    c_miss=miss,
                    c_fa=fa,
                    normalized=normalized,
                )
                expected = min(costs) / (min(miss * prior, fa * (1 - prior)) if normalized else 1)
                self.assertAlmostEqual(result["value"], expected, places=12)

    def test_invalid_trials(self):
        for scores, labels in (
            ([], []),
            ([1], [1]),
            ([1, np.nan], [0, 1]),
            ([1, 2], [0, 2]),
            ([[1, 2]], [0, 1]),
            ([1, 2], [0]),
        ):
            for metric in ("eer", "min_dcf"):
                self.assertEqual(
                    run(metric, scores=scores, labels=labels, p_target=0.01)["status"],
                    "invalid_input",
                )
        self.assertEqual(
            run("eer", scores=[1, 2], labels=[0, 1], trial_ids=["a", "a"])["status"],
            "invalid_input",
        )

    def test_prior_and_endpoints(self):
        for prior in (None, 0, 1, -1, True, np.nan):
            self.assertEqual(
                run("min_dcf", scores=[1, 1], labels=[0, 1], p_target=prior)["status"],
                "invalid_input",
            )
        result = run("min_dcf", scores=[1, 1], labels=[0, 1], p_target=0.01)
        self.assertEqual(result["value"], 1)
        self.assertEqual(result["details"]["decision"], "reject_all")
        self.assertIsNone(result["details"]["threshold"])
        for metric in ("eer", "min_dcf"):
            with self.assertRaises(ValueError):
                evaluate_batch(metric, [])


class ERLETests(unittest.TestCase):
    def settings(self):
        return dict(sample_rate=10, farend_only_regions=[[0, 1]], signal_definition="isolated_echo")

    def test_masked_gain_and_non_normalization(self):
        x = np.ones(20)
        y = np.r_[np.ones(10) * 0.1, np.ones(10) * 20]
        self.assertAlmostEqual(
            run("erle", reference=x, hypothesis=y, **self.settings())["value"], 20
        )
        self.assertAlmostEqual(
            run("erle", reference=x, hypothesis=x * 2, **self.settings())["value"],
            -20 * np.log10(2),
        )

    def test_energy_pooling_including_zero_residual(self):
        rows = [
            {"id": str(i), "inputs": {"reference": [1] * 10, "hypothesis": [gain] * 10}}
            for i, gain in enumerate((0.0, 0.5))
        ]
        result = evaluate_batch("erle", rows, **self.settings())
        self.assertTrue(result["complete"])
        self.assertAlmostEqual(result["value"], 10 * np.log10(20 / 2.5))
        self.assertEqual(result["aggregation"], "micro_energy_ratio_db")

    def test_silence_and_invalid_regions(self):
        settings = self.settings()
        for before, after, status in (
            ([0] * 10, [0] * 10, "undefined_reference"),
            ([1] * 10, [0] * 10, "infinite_result"),
        ):
            result = run("erle", reference=before, hypothesis=after, **settings)
            self.assertEqual(result["status"], status)
            self.assertIsNone(result["value"])
            json.dumps(result, allow_nan=False)
        for regions in ([], [[0, 2]], [[0, 0.5], [0.4, 1]], [[0, 0]], [[0, np.inf]]):
            settings["farend_only_regions"] = regions
            self.assertEqual(
                run("erle", reference=[1] * 10, hypothesis=[0.1] * 10, **settings)["status"],
                "invalid_input",
            )

    def test_protocol_mixing_rejected_and_failures_retained(self):
        rows = [
            {
                "id": str(i),
                "inputs": {
                    "reference": [1] * 10,
                    "hypothesis": [0.1] * 10,
                    "signal_definition": definition,
                },
            }
            for i, definition in enumerate(("isolated_echo", "microphone_farend_only"))
        ]
        with self.assertRaises(ValueError):
            evaluate_batch("erle", rows, **self.settings())
        rows[1]["inputs"] = {"reference": [0] * 10, "hypothesis": [0] * 10}
        result = evaluate_batch("erle", rows, **self.settings())
        self.assertFalse(result["complete"])
        self.assertIsNone(result["value"])
        self.assertEqual(result["coverage"], 0.5)


class DeploymentTests(unittest.TestCase):
    def test_lock_and_tamper(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.py"
            source.write_text("# fixture\n")
            lock = create_deployment({"aecmos_16k": {"source_file": str(source)}})
            self.assertEqual(verify_deployment(lock)["status"], "ok")
            missing = copy.deepcopy(lock)
            missing["configs"]["aecmos_16k"]["expected_hashes"] = {}
            self.assertEqual(verify_deployment(missing)["status"], "deployment_mismatch")
            changed = copy.deepcopy(lock)
            changed["environment"]["python"] = "0"
            self.assertEqual(verify_deployment(changed)["status"], "deployment_mismatch")
            source.write_text("# changed\n")
            self.assertEqual(verify_deployment(lock)["status"], "deployment_mismatch")

    def test_library_lock_and_unknown_family(self):
        lock = create_deployment({})
        self.assertEqual(verify_deployment(lock)["status"], "ok")
        lock["environment"]["library_sha256"] = "0"
        self.assertEqual(verify_deployment(lock)["status"], "deployment_mismatch")
        with self.assertRaises(ValueError):
            create_deployment({"unknown": {}})

    def test_shared_aec_forward_pass(self):
        from speechmetrichub import evaluate

        with patch(
            "speech_eval.aec.aecmos_family",
            return_value={"status": "ok", "values": {"echo_mos": 3, "deg_mos": 4}},
        ) as worker:
            result = evaluate(
                ["aecmos_16k_echo", "aecmos_16k_deg"],
                hypothesis="enh.wav",
                farend="far.wav",
                microphone="mic.wav",
                talk_type="dt",
            )
            self.assertEqual(worker.call_count, 1)
            self.assertEqual(result["aecmos_16k_deg"]["value"], 4)

    def test_cli_missing_input_nonzero_json(self):
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "speechmetrichub",
                "run",
                "eer",
                "--input",
                "/missing/smh-test-input.json",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "invalid_request")

    def test_mixed_aec_and_erle_input_routing(self):
        from speechmetrichub import evaluate

        with patch(
            "speech_eval.aec.aecmos_family",
            return_value={"status": "ok", "values": {"echo_mos": 3}},
        ):
            result = evaluate(
                ["aecmos_16k_echo", "erle"],
                hypothesis=[0.1] * 10,
                reference=[1] * 10,
                farend="far.wav",
                microphone="mic.wav",
                talk_type="st",
                sample_rate=10,
                farend_only_regions=[[0, 1]],
                signal_definition="isolated_echo",
            )
            self.assertAlmostEqual(result["erle"]["value"], 20)

    def test_malformed_manifest_and_worker_parameters(self):
        from speech_eval.models import model_family

        self.assertEqual(verify_deployment([])["status"], "deployment_mismatch")
        for config in ({"device": 3}, {"timeout": float("nan")}, {"timeout": 0}, {"threads": True}):
            with self.assertRaises(ValueError):
                model_family("aecmos_16k", hypothesis="missing.wav", config=config)
