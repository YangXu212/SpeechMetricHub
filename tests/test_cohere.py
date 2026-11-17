"""Cohere scoring contracts; real model parity is in validate_cohere.py."""

import tempfile
import copy
import importlib.util
import json
import os
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np

from speech_eval.cohere import (
    _reassemble,
    compare_text,
    generation_health,
    generation_limits,
    finalize_score,
    read_audio,
    settings,
    score,
)


class CohereContractTests(unittest.TestCase):
    def test_optional_profiles_do_not_change_existing_defaults(self):
        legacy = settings({})
        self.assertEqual(legacy["normalizer"], "nfkc-casefold-v1")
        self.assertEqual(legacy["truncation_policy"], "reject")
        self.assertEqual(legacy["audio_frontend"], "strict_float32")
        self.assertTrue(legacy["punctuation"])
        for family in ("cohere_wer_en_whisper", "cohere_dwer_en_whisper"):
            configured = settings({}, family)
            self.assertEqual(configured["normalizer"], "whisper_en")
            self.assertFalse(configured["punctuation"])
            self.assertEqual(configured["truncation_policy"], "score")
            self.assertEqual(configured["audio_frontend"], "float64_downmix")
            with self.assertRaises(ValueError):
                settings({"language": "zh"}, family)
        for family in ("cohere_cer_zh_basic", "cohere_dcer_zh_basic"):
            configured = settings({}, family)
            self.assertEqual(configured["language"], "zh")
            self.assertEqual(configured["normalizer"], "whisper_basic")
        configured = settings(
            {"truncation_policy": "reject", "punctuation": True}, "cohere_wer_en_whisper"
        )
        self.assertEqual(configured["truncation_policy"], "reject")
        self.assertTrue(configured["punctuation"])

    def test_declared_truncation_policy_preserves_denominator_and_diagnostics(self):
        original = {
            "details": {
                "reference_text": "one two three",
                "hypothesis_text": "one",
                "hypothesis_decode": {"complete": False},
                "reference_decode": None,
            }
        }
        rejected = finalize_score(copy.deepcopy(original))
        self.assertEqual(rejected["status"], "generation_truncated")
        self.assertEqual(rejected["values"], {})
        scored = finalize_score(copy.deepcopy(original), truncation_policy="score")
        self.assertEqual(scored["status"], "ok")
        self.assertEqual(scored["details"]["word"]["N"], 3)
        self.assertEqual(scored["details"]["word"]["D"], 2)
        self.assertFalse(scored["details"]["generation_complete"])
        self.assertTrue(scored["details"]["scored_truncated_generation"])
        self.assertTrue(scored["warnings"])
        original["details"]["reference_text"] = ""
        empty = finalize_score(copy.deepcopy(original), truncation_policy="score")
        self.assertEqual(empty["status"], "undefined_reference")
        self.assertEqual(empty["details"]["word"]["I"], 1)

    def test_generation_budget_uses_actual_decoder_capacity_and_prompt(self):
        decoder = SimpleNamespace(config=SimpleNamespace(max_position_embeddings=32))
        model = SimpleNamespace(
            generation_config=SimpleNamespace(decoder_start_token_id=7),
            config=SimpleNamespace(),
            get_decoder=lambda: decoder,
        )
        self.assertEqual(generation_limits(model, [[7, 8, 9]], 29), (3, 32))
        with self.assertRaises(ValueError):
            generation_limits(model, [[7, 8, 9]], 30)
        # GenerationMixin inserts the missing start token before the supplied prompt.
        self.assertEqual(generation_limits(model, [[8, 9]], 29), (3, 32))
        decoder.config.max_position_embeddings = 1024
        self.assertEqual(generation_limits(model, [[7] * 10], 512), (10, 1024))

    def test_float64_frontend_preserves_downmix_resample_order(self):
        import soundfile as sf
        import soxr

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "stereo.wav"
            audio = np.random.default_rng(4).normal(0, 0.03, (24000, 2))
            sf.write(path, audio, 24000, subtype="DOUBLE")
            decoded, rate = sf.read(path)
            expected = np.ascontiguousarray(
                soxr.resample(decoded.mean(axis=-1), rate, 16000), dtype=np.float32
            )
            actual, _ = read_audio(path, frontend="float64_downmix")
            np.testing.assert_array_equal(actual, expected)
            self.assertEqual(actual.dtype, np.float32)
            self.assertTrue(actual.flags.c_contiguous)
            with self.assertRaises(ValueError):
                read_audio(path)

    @unittest.skipUnless(
        all(importlib.util.find_spec(p) for p in ("espnet2", "whisper", "Levenshtein")),
        "Optional upstream text cleaners",
    )
    def test_upstream_normalizers_are_not_followed_by_generic_normalization(self):
        from espnet2.text.cleaner import TextCleaner
        import Levenshtein

        reference, hypothesis = "It's $2.50 and twenty-one apples.", "It is $2.50 and 21 apples."
        actual = compare_text(reference, hypothesis, normalizer="whisper_en")
        cleaner = TextCleaner("whisper_en")
        expected_reference = cleaner(reference)
        self.assertEqual(actual["word"]["normalized_reference_text"], expected_reference)
        self.assertEqual(actual["word"]["reference_tokens"], expected_reference.split())
        self.assertTrue(any("$" in token for token in actual["word"]["reference_tokens"]))
        self.assertEqual(
            actual["word"]["errors"],
            Levenshtein.distance(cleaner(reference).split(), cleaner(hypothesis).split()),
        )
        chinese = compare_text("我有二十一元。", "我有21元", normalizer="whisper_basic")
        self.assertGreater(chinese["char"]["errors"], 0)  # No English number conversion.
        expected = TextCleaner("whisper_basic")("我有二十一元。")
        self.assertEqual(
            chinese["char"]["reference_tokens"], [c for c in expected if not c.isspace()]
        )
        self.assertEqual(len(chinese["char"]["reference_fingerprint"]), 64)

    def test_routed_dispatcher_uses_worker_environment_and_preserves_gpu_mapping(self):
        from speech_eval.models import model_family

        observed = []

        def invoke(command, **kwargs):
            request = json.loads(Path(command[-2]).read_text(encoding="utf-8"))
            observed.append((command, kwargs["env"], request))
            Path(command[-1]).write_text('{"status": "ok", "values": {"wer": 0}}')
            return SimpleNamespace(returncode=0, stderr="")

        config = {
            "python": "/isolated/cohere/bin/python",
            "worker_deployment": "worker.locked.json",
            "device": "cuda:3",
        }
        with patch.dict(os.environ, {"PYTHONPATH": "/wrong/base/site-packages"}):
            with patch("speech_eval.models.subprocess.run", side_effect=invoke):
                result = model_family(
                    "cohere_wer", hypothesis="audio.wav", reference="text", config=config
                )
                model_family("whisper_wer", hypothesis="audio.wav", reference="text")
        command, environment, request = observed[0]
        self.assertEqual(command[0], config["python"])
        self.assertNotIn("PYTHONPATH", environment)
        self.assertEqual(environment["CUDA_VISIBLE_DEVICES"], "3")
        self.assertEqual(request["config"]["device"], "cuda:0")
        self.assertEqual(result["execution"]["device"], "cuda:3")
        self.assertEqual(config["device"], "cuda:3")
        # The established same-environment worker retains its source path behavior.
        self.assertIn("PYTHONPATH", observed[1][1])
        self.assertIn("/wrong/base/site-packages", observed[1][1]["PYTHONPATH"])
        self.assertEqual(observed[1][1]["CUDA_VISIBLE_DEVICES"], "")

    def test_unchunked_blank_text_is_preserved_and_only_chunked_empty_bug_is_guarded(self):
        processor = SimpleNamespace(
            tokenizer=SimpleNamespace(decode=Mock(return_value=[" "])),
            decode=Mock(return_value=[" "]),
        )
        self.assertEqual(_reassemble(processor, [[1, 2]], [(0, None)], "en"), (" ", False))
        processor.decode.assert_called_once()
        processor.tokenizer.decode.return_value = [" ", ""]
        processor.decode.reset_mock()
        processor.decode.side_effect = IndexError("native non_empty[0]")
        self.assertEqual(_reassemble(processor, [[1], [2]], [(0, 0), (0, 1)], "en"), ("", True))
        processor.decode.assert_not_called()

    def test_worker_manifest_parent_pin_is_checked_before_model_loading(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "worker.json"
            path.write_text("{}")
            result = score(
                {
                    "family": "cohere_wer",
                    "config": {
                        "worker_deployment": str(path),
                        "expected_hashes": {"worker_deployment": "0" * 64},
                    },
                }
            )
            self.assertEqual(result["status"], "deployment_mismatch")
            self.assertIn("parent pin", result["reason"])

    def test_word_and_character_heads_are_distinct(self):
        result = compare_text("A cat!", "a bat")
        self.assertEqual(result["word"]["value"], 50)
        self.assertEqual(result["word"]["N"], 2)
        self.assertEqual(result["char"]["value"], 25)
        self.assertEqual(result["char"]["N"], 4)

    def test_generic_normalization_and_no_number_verbalization(self):
        self.assertEqual(compare_text("Ａ CAT!", "a cat")["word"]["errors"], 0)
        self.assertEqual(compare_text("2 cats", "two cats")["word"]["S"], 1)
        result = compare_text("你好世界", "你好世间")
        self.assertEqual(result["char"]["value"], 25)
        self.assertEqual(result["word"]["N"], 1)  # Explicitly no invented Chinese segmentation.

    def test_empty_reference_retains_hallucination_insertions(self):
        result = compare_text("", "hello world")
        self.assertEqual(result["word"]["status"], "undefined_reference")
        self.assertIsNone(result["word"]["value"])
        self.assertEqual(result["word"]["I"], 2)
        self.assertEqual(result["char"]["I"], 10)
        self.assertEqual(compare_text("hello world", "")["word"]["D"], 2)
        self.assertEqual(compare_text("hello world", "")["word"]["value"], 100)
        self.assertIsNone(compare_text("", "")["word"]["value"])

    def test_decode_settings_reject_ambiguous_or_ignored_options(self):
        default = settings({})
        self.assertEqual(
            (default["dtype"], default["language"], default["beam_size"]), ("float32", "en", 1)
        )
        self.assertEqual(settings({"device": "cuda:1"})["dtype"], "bfloat16")
        for cfg in (
            {"device": "cuda"},
            {"dtype": "bfloat16"},
            {"language": "english"},
            {"language": "auto"},
            {"beam_size": True},
            {"max_new_tokens": 0},
            {"punctuation": 1},
            {"chunk_batch_size": False},
            {"max_audio_seconds": float("inf")},
            {"max_audio_seconds": True},
            {"do_sample": True},
            {"vad": True},
        ):
            with self.assertRaises(ValueError, msg=str(cfg)):
                settings(cfg)

    def test_generation_cap_does_not_silently_score_partial_transcription(self):
        # The first EOS is in a prompt, so it cannot establish completion.
        result = generation_health([[9, 1, 2, 9, 0], [9, 1, 2, 3, 4]], 2, 9)
        self.assertFalse(result["complete"])
        self.assertEqual(result["missing_eos_chunks"], [1])
        self.assertEqual(result["generated_tokens_per_chunk"], [2, 3])
        result = generation_health([[1, 2, 8, 0], [1, 2, 3, 9]], 2, [8, 9])
        self.assertTrue(result["complete"])
        with self.assertRaises(ValueError):
            generation_health([[1]], 0, None)

    def test_audio_accepts_silence_but_rejects_stereo_corruption_and_overlength(self):
        import soundfile as sf

        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "probe.wav"
            sf.write(path, np.zeros(24000), 24000)
            wave, info = read_audio(path)
            self.assertEqual(len(wave), 16000)
            self.assertTrue(info["exact_zero_waveform"])
            self.assertFalse(np.any(wave))
            with self.assertRaises(ValueError):
                read_audio(path, maximum=0.5)
            sf.write(path, np.zeros((16000, 2)), 16000)
            with self.assertRaises(ValueError):
                read_audio(path)
            wave = np.zeros(16000)
            wave[100] = np.nan
            sf.write(path, wave, 16000, subtype="FLOAT")
            with self.assertRaises(ValueError):
                read_audio(path)


if __name__ == "__main__":
    unittest.main()
