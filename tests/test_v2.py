import unittest
from speech_eval import list_metrics, run
from speech_eval.models import select
from speech_eval.batch import evaluate_batch


class RegistryTests(unittest.TestCase):
    def test_taxonomy_and_ids(self):
        rows = list_metrics()
        self.assertEqual(len(rows), len({m["id"] for m in rows}))
        for row in rows:
            self.assertNotIn(row["category"], ["enhancement", "tse", "codec"])
            self.assertTrue(row["reference_kinds"])
            self.assertIn(row["direction"], ["lower_is_better", "higher_is_better", "descriptive"])
        self.assertEqual(len(list_metrics(category="audio_aesthetics")), 4)

    def test_full_heads_and_directions(self):
        rows = {m["id"]: m for m in list_metrics()}
        for axis in ("ce", "cu", "pc", "pq"):
            self.assertIn("audiobox_aesthetics_" + axis, rows)
        self.assertEqual(rows["audiobox_aesthetics_pc"]["direction"], "descriptive")
        for domain in ("natural", "synthetic"):
            self.assertEqual(rows[f"scoreq_{domain}_ref"]["direction"], "lower_is_better")
            self.assertEqual(rows[f"scoreq_{domain}_nr"]["direction"], "higher_is_better")
        for head in ("precision", "recall", "f1"):
            self.assertIn("speechbert_" + head, rows)

    def test_missing_head_is_error(self):
        result = select(
            {"status": "ok", "values": {}},
            dict(
                id="example",
                output="missing",
                family="test",
                unit="ratio",
                direction="higher_is_better",
            ),
        )
        self.assertEqual(result["status"], "backend_error")


class StandardTests(unittest.TestCase):
    def test_timing_changes_time_constrained_orc(self):
        ref = [{"speaker": "a", "start": 0.0, "end": 1.0, "text": "one two"}]
        hyp = [{"speaker": "x", "start": 10.0, "end": 11.0, "text": "one two"}]
        self.assertEqual(run("orcwer", reference=ref, hypothesis=hyp)["value"], 0)
        self.assertEqual(run("tcorcwer", reference=ref, hypothesis=hyp, collar=1)["errors"], 4)

    def test_waveform_invalid_inputs_are_not_scores(self):
        import numpy as np

        for metric in ("pesq_wb", "pesq_nb", "stoi", "estoi", "si_sdr", "si_sdri"):
            for reference, hypothesis in [
                (np.zeros(16000), np.ones(16000)),
                (np.ones(16000), np.ones(8000)),
                (np.ones(16000), np.full(16000, np.nan)),
            ]:
                result = run(metric, reference=reference, hypothesis=hypothesis, sample_rate=16000)
                self.assertNotEqual(result["status"], "ok")
                self.assertIsNone(result["value"])

    def test_der_timing_is_not_only_labels(self):
        ref = [{"speaker": "a", "start": 0.0, "end": 2.0}]
        hyp = [{"speaker": "x", "start": 1.0, "end": 2.0}]
        value = run(
            "der", reference=ref, hypothesis=hyp, uem=[[0, 2]], reference_is_speech_activity=True
        )["value"]
        self.assertEqual(value, 50.0)

    def test_bss_no_permutation(self):
        import numpy as np

        rng = np.random.default_rng(1)
        a = rng.normal(size=(2, 2000))
        b = a + 0.1 * rng.normal(size=a.shape)
        result = run("bss_sdr", reference=a, hypothesis=b, filter_length=16, permutation=False)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["permutation"], [0, 1])

    def test_der_micro_and_different_uem(self):
        def row(key, duration, detected):
            return {
                "id": key,
                "inputs": {
                    "reference": [{"speaker": "a", "start": 0, "end": duration}],
                    "hypothesis": [{"speaker": "x", "start": 0, "end": detected}],
                    "uem": [[0, duration]],
                },
            }

        result = evaluate_batch(
            "der", [row("short", 2, 1), row("long", 10, 10)], reference_is_speech_activity=True
        )
        self.assertAlmostEqual(result["value"], 100 / 12)
        self.assertEqual(result["aggregation"], "micro_pyannote_components")

    def test_rating_dataset_not_macro(self):
        with self.assertRaises(ValueError):
            evaluate_batch("plcc", [])

    def test_invalid_correlation(self):
        self.assertEqual(
            run("plcc", reference=[1, 1, 1], hypothesis=[2, 3, 4])["status"], "undefined_constant"
        )


if __name__ == "__main__":
    unittest.main()
