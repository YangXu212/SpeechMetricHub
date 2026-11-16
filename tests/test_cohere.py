"""Cohere scoring contracts; real model parity is in validate_cohere.py."""

import tempfile
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
    read_audio,
    settings,
    score,
)


class CohereContractTests(unittest.TestCase):
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
