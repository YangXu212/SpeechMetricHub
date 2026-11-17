import copy
import unittest

from speech_eval.comparison import compare_recognition


def result(n=2, s=0, d=0, i=0, text="one two", **changes):
    value = {
        "metric": "cohere_wer",
        "status": "ok" if n else "undefined_reference",
        "N": n,
        "S": s,
        "D": d,
        "I": i,
        "errors": s + d + i,
        "value_unit": "percent",
        "backend": {"meeteval": "0.4.3", "transformers": "5.4.0"},
        "protocol": {
            "normalization": "nfkc-casefold-v1",
            "model": "fixed-recognizer",
            "beam_size": 1,
        },
        "details": {"reference_text": text, "hypothesis_decode": {"complete": True}},
    }
    value.update(changes)
    return value


def row(key="a", **changes):
    return {"id": key, "result": result(**changes)}


class RecognitionComparisonTests(unittest.TestCase):
    def test_complete_micro_counts(self):
        a = [row("short", n=1, s=1, text="one"), row("long", n=3, text="one two three")]
        b = [row("short", n=1, text="one"), row("long", n=3, s=1, text="one two three")]
        report = compare_recognition({"a": a, "b": b}, expected_ids=["short", "long"])
        self.assertTrue(report["full_corpus_comparable"])
        self.assertEqual(report["systems"]["a"]["value"], 25)
        self.assertEqual(report["systems"]["b"]["value"], 25)
        self.assertIsNone(report["ranking"])

    def test_strict_failure_does_not_shrink_full_corpus(self):
        bad = {
            "id": "b",
            "result": {
                "status": "generation_truncated",
                "reason": "No EOS",
                "details": {"hypothesis_decode": {"complete": False}},
            },
        }
        report = compare_recognition(
            {"a": [row(), bad], "b": [row(), row("b", s=1)]}, expected_ids=["a", "b"]
        )
        self.assertIsNone(report["systems"]["a"]["value"])
        self.assertEqual(report["systems"]["b"]["value"], 25)
        self.assertFalse(report["full_corpus_comparable"])
        self.assertEqual(report["common_subset"]["ids"], ["a"])
        self.assertTrue(report["common_subset"]["diagnostic_only"])
        self.assertEqual(report["systems"]["a"]["truncated"], 1)
        self.assertEqual(report["systems"]["a"]["truncation_rate"], 0.5)

    def test_named_profile_uses_explicit_scoring_unit(self):
        entry = row(metric="cohere_wer_en_whisper", scoring_unit="word")
        report = compare_recognition(
            {"a": [entry], "b": [copy.deepcopy(entry)]}, expected_ids=["a"]
        )
        self.assertTrue(report["full_corpus_comparable"])

    def test_scoreable_truncation_retains_errors(self):
        partial = row(
            s=1, details={"reference_text": "one two", "hypothesis_decode": {"complete": False}}
        )
        report = compare_recognition({"a": [partial], "b": [row()]}, expected_ids=["a"])
        self.assertTrue(report["full_corpus_comparable"])
        self.assertEqual(report["systems"]["a"]["value"], 50)
        self.assertEqual(report["systems"]["a"]["scored_truncated"], 1)

    def test_generic_scored_truncation_flags_are_diagnostic(self):
        partial = row(s=1, details={"reference_text": "one two", "generation_complete": False})
        report = compare_recognition({"a": [partial], "b": [row()]}, expected_ids=["a"])
        self.assertEqual(report["systems"]["a"]["value"], 50)
        self.assertEqual(report["systems"]["a"]["scored_truncated"], 1)

    def test_expected_ids_detect_shared_omission(self):
        report = compare_recognition({"a": [row()], "b": [row()]}, expected_ids=["a", "missing"])
        for system in report["systems"].values():
            self.assertEqual(system["failures_by_status"], {"missing_result": 1})
            self.assertIsNone(system["value"])
        self.assertEqual(report["common_subset"]["coverage"], 0.5)

    def test_shared_omission_without_manifest_never_claims_full_corpus(self):
        # Both systems may have omitted the same difficult examples. A perfect
        # observed set cannot establish full-corpus accuracy or coverage.
        report = compare_recognition({"a": [row()], "b": [row()]})
        self.assertFalse(report["expected_corpus_verified"])
        self.assertFalse(report["full_corpus_comparable"])
        self.assertIn("expected_corpus_unverified", report["comparability_issues"])
        for system in report["systems"].values():
            self.assertTrue(system["counts_complete"])
            self.assertFalse(system["complete"])
            self.assertIsNone(system["value"])
            self.assertEqual(system["valid_subset_value"], 0)
            self.assertTrue(system["valid_subset_diagnostic_only"])
        subset = report["common_subset"]
        self.assertTrue(subset["diagnostic_only"])
        self.assertTrue(subset["comparable_within_subset"])
        self.assertEqual(subset["systems"]["a"]["value"], 0)

    def test_union_keeps_asymmetric_omission(self):
        report = compare_recognition({"a": [row()], "b": [row(), row("b")]})
        self.assertEqual(report["expected_ids"], ["a", "b"])
        self.assertIn("shared by every system", report["corpus_scope"])
        self.assertFalse(report["full_corpus_comparable"])

    def test_duplicate_and_unexpected_ids_rejected(self):
        with self.assertRaises(ValueError):
            compare_recognition({"a": [row(), row()]})
        with self.assertRaises(ValueError):
            compare_recognition({"a": [row()]}, expected_ids=["a", "a"])
        with self.assertRaises(ValueError):
            compare_recognition({"a": [row()]}, expected_ids=[])

    def test_empty_reference_insertions_retained(self):
        a = [row("silent", n=0, i=2, text=""), row("speech")]
        b = [row("silent", n=0, text=""), row("speech")]
        report = compare_recognition({"a": a, "b": b}, expected_ids=["silent", "speech"])
        self.assertTrue(report["full_corpus_comparable"])
        self.assertEqual(report["systems"]["a"]["value"], 100)
        self.assertEqual(report["systems"]["a"]["counts"]["I"], 2)

    def test_different_reference_with_same_length_is_rejected(self):
        report = compare_recognition({"a": [row()], "b": [row(text="three four")]})
        self.assertFalse(report["full_corpus_comparable"])
        self.assertIsNone(report["common_subset"]["systems"]["a"]["value"])
        self.assertEqual(report["reference_issues"][0]["reason"], "reference_identities_differ")

    def test_reference_identity_cannot_be_inferred_from_counts(self):
        report = compare_recognition({"a": [row(details={})], "b": [row(details={})]})
        self.assertFalse(report["full_corpus_comparable"])
        self.assertEqual(report["reference_issues"][0]["reason"], "reference_identity_unverified")

    def test_caller_reference_id_supported_and_disclosed(self):
        a, b = row(details={}), row(details={})
        a["reference_id"] = b["reference_id"] = "annotations-v1:a"
        report = compare_recognition({"a": [a], "b": [b]}, expected_ids=["a"])
        self.assertTrue(report["full_corpus_comparable"])
        self.assertEqual(report["reference_identity_evidence"]["a"], ["caller_reference_id"])

    def test_reference_fingerprint_supported(self):
        a = row(details={"reference_fingerprint": {"word": "fixed-token-hash"}})
        report = compare_recognition({"a": [a], "b": [copy.deepcopy(a)]}, expected_ids=["a"])
        self.assertTrue(report["full_corpus_comparable"])

    def test_reference_tokens_must_match_N(self):
        report = compare_recognition({"a": [row(n=3)], "b": [row(n=3)]})
        self.assertFalse(report["full_corpus_comparable"])
        self.assertEqual(
            report["reference_issues"][0]["reason"], "reference_tokens_disagree_with_N"
        )

    def test_asr_protocol_backend_and_units_must_match(self):
        for field, value in (
            (
                "protocol",
                {
                    "normalization": "nfkc-casefold-v1",
                    "model": "another-recognizer",
                    "beam_size": 1,
                },
            ),
            ("backend", {"meeteval": "0.4.2", "transformers": "5.4.0"}),
            ("metric", "cohere_cer"),
        ):
            report = compare_recognition({"a": [row()], "b": [row(**{field: value})]})
            self.assertFalse(report["protocol_compatible"])
            self.assertFalse(report["full_corpus_comparable"])

    def test_invalid_counts_are_failure_not_success(self):
        for changes in ({"N": -1}, {"errors": 4}, {"S": True}, {"N": 1, "S": 2, "errors": 2}):
            bad = row()
            bad["result"].update(changes)
            report = compare_recognition({"a": [bad], "b": [row()]})
            self.assertEqual(report["systems"]["a"]["scored"], 0)
            self.assertIsNone(report["systems"]["a"]["value"])

    def test_empty_corpus_is_not_comparable(self):
        report = compare_recognition({"a": [], "b": []}, expected_ids=[])
        self.assertFalse(report["full_corpus_comparable"])
        self.assertIsNone(report["systems"]["a"]["value"])

    def test_malformed_metadata_does_not_hide_results_or_crash(self):
        for changes in ({"protocol": "invalid"}, {"details": {"word": "invalid"}}):
            report = compare_recognition({"a": [row(**changes)], "b": [row()]})
            self.assertFalse(report["full_corpus_comparable"])
        report = compare_recognition({"a": [row(status={"bad": "status"})], "b": [row()]})
        self.assertEqual(report["systems"]["a"]["scored"], 0)
        with self.assertRaises(ValueError):
            compare_recognition({"a": [row()]}, expected_ids="a")

    def test_inputs_not_mutated_and_selected_ids_are_fingerprinted(self):
        systems = {"a": [row()], "b": [row()]}
        before = copy.deepcopy(systems)
        report = compare_recognition(systems)
        self.assertEqual(systems, before)
        self.assertEqual(len(report["expected_ids_sha256"]), 64)
        self.assertEqual(report["expected_ids_sha256"], report["common_subset"]["ids_sha256"])


if __name__ == "__main__":
    unittest.main()
