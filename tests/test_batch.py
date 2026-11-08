import unittest
from speech_eval.batch import evaluate_batch
from speech_eval import run


class BatchTests(unittest.TestCase):
    def test_micro_and_failure(self):
        rows = [
            {"id": "a", "inputs": {"reference": "one", "hypothesis": ""}},
            {"id": "b", "inputs": {"reference": "one two three", "hypothesis": "one two three"}},
        ]
        result = evaluate_batch("wer", rows)
        self.assertEqual(result["value"], 25)
        rows.append({"id": "invalid", "inputs": {}})
        result = evaluate_batch("wer", rows)
        self.assertFalse(result["complete"])
        self.assertIsNone(result["value"])
        self.assertEqual(len(result["rows"]), 3)

    def test_empty_reference_insertions_not_dropped(self):
        result = evaluate_batch(
            "wer",
            [
                {"id": "a", "inputs": {"reference": "", "hypothesis": "extra"}},
                {"id": "b", "inputs": {"reference": "one", "hypothesis": "one"}},
            ],
        )
        self.assertEqual(result["value"], 100)

    def test_target_requires_target_only(self):
        with self.assertRaises(ValueError):
            run(
                "ts_wer",
                reference=[{"speaker": "a", "text": "one"}, {"speaker": "b", "text": "two"}],
                hypothesis="one",
            )

    def test_mixed_collars_rejected(self):
        r = [{"speaker": "a", "text": "hi", "start": 0, "end": 1}]
        with self.assertRaises(ValueError):
            evaluate_batch(
                "tcpwer",
                [
                    {"id": "a", "inputs": {"reference": r, "hypothesis": r, "collar": 2}},
                    {"id": "b", "inputs": {"reference": r, "hypothesis": r, "collar": 5}},
                ],
            )
