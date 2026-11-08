import unittest
from speech_eval.transcription import evaluate, score
from speech_eval.aggregate import aggregate
from speech_eval import run


def s(w, speaker="a", start=0, end=1):
    return dict(text=w, speaker=speaker, start=start, end=end)


class TranscriptionTests(unittest.TestCase):
    def test_global_permutation(self):
        r = [s("one two", "a", 0, 2), s("three four", "b", 0, 2)]
        h = [s("three four", "x", 0, 2), s("one two", "y", 0, 2)]
        self.assertEqual(score(r, h)["errors"], 0)
        self.assertEqual(score(r, h, collar=5)["errors"], 0)

    def test_merge_and_split(self):
        r = [s("one two", "a"), s("three four", "b", 2, 3)]
        h = [s("one two", "x"), s("three four", "x", 2, 3)]
        self.assertGreater(score(r, h)["errors"], 0)
        self.assertGreater(score(h, r)["errors"], 0)

    def test_no_per_sentence_reassignment(self):
        r = [s("one", "a", 0, 1), s("two", "b", 2, 3), s("three", "a", 4, 5)]
        h = [s("one", "x", 0, 1), s("two", "y", 2, 3), s("three", "y", 4, 5)]
        self.assertGreater(score(r, h)["errors"], 0)

    def test_time_shift(self):
        r = [s("hello")]
        h = [s("hello", "x", 20, 21)]
        self.assertEqual(score(r, h)["errors"], 0)
        self.assertEqual(score(r, h, collar=5)["errors"], 2)

    def test_cer(self):
        m = score([s("你好，世界")], [s("你好，世间")], unit="char")
        self.assertEqual((m["N"], m["errors"]), (4, 1))

    def test_empty(self):
        for collar in [None, 5]:
            self.assertEqual(score([s("one two")], [], collar=collar)["D"], 2)
            self.assertEqual(score([], [s("one two")], collar=collar)["I"], 2)
            self.assertIsNone(score([], [], collar=collar)["rate"])

    def test_target_no_best_match(self):
        self.assertEqual(run("ts_wer", reference="hello", hypothesis="bye")["errors"], 1)

    def test_raw_tail(self):
        m = evaluate([s("hello")], [s("hello")], raw="[0][S1]hello[1][2][S1]never closed")
        self.assertFalse(m["metrics"]["cp_wer"]["eligible"])
        self.assertEqual(m["generation"]["status"], "unparsed_text")

    def test_invalid_timing(self):
        m = evaluate([s("hello")], [s("hello", "a", 0, 3)], duration=1)
        self.assertFalse(m["timing"]["available"])
        self.assertIn("cp_wer", m["metrics"])
        self.assertNotIn("tcp_wer_5s", m["metrics"])

    def test_strict_coverage(self):
        e = evaluate([s("hello")], [], raw="")
        bad = evaluate([s("hello")], [s("hello", "a", 0, 3)], duration=1)
        m = aggregate(
            [dict(name="one", evaluation=e), dict(name="bad", evaluation=bad)], "tcp_wer_5s"
        )
        self.assertEqual(m["coverage"], 0.5)
        self.assertIsNone(m["complete_set_rate"])

    def test_micro_weighting(self):
        a = evaluate([s("one")], [], raw="")
        b = evaluate([s("one two three")], [s("one two three")])
        m = aggregate([dict(evaluation=a), dict(evaluation=b)], "cp_wer")
        self.assertEqual(m["complete_set_rate"], 25)

    def test_boundary_and_no_reference(self):
        self.assertFalse(
            evaluate([s("hi")], [s("hi")], boundary_note="partial")["metrics"]["cp_wer"]["eligible"]
        )
        self.assertFalse(evaluate([], [], has_reference=False)["available"])


if __name__ == "__main__":
    unittest.main()
