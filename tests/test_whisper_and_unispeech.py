"""Contracts for OpenAI Whisper, upgraded HF Whisper v3 and UniSpeech WavLM-ECAPA."""

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from speech_eval.comparison import compare_recognition
from speech_eval.deployment import create_deployment, verify_deployment
from speech_eval.models import select
from speech_eval.registry import get_metric
from speech_eval.whisper_asr import (
    DEFAULT_HF_TEMPERATURES,
    score_text,
    settings,
)


class _DummyTokenizer:
    def normalize(self, text):
        return text.lower().replace("colour", "color").replace(".", "").strip()


class WhisperProfileContractTests(unittest.TestCase):
    def test_openai_and_hf_v3_defaults_and_validation(self):
        for family in ("whisper_wer_en_openai", "whisper_dwer_en_openai"):
            cfg = settings({}, family)
            self.assertEqual(cfg["backend_kind"], "openai")
            self.assertEqual(cfg["device"], "cpu")
            self.assertEqual(cfg["dtype"], "float32")
            self.assertEqual(cfg["language"], "en")
            self.assertEqual(cfg["beam_size"], 5)
            self.assertEqual(cfg["hallucination_silence_threshold"], 2.0)
            self.assertEqual(cfg["normalizer"], "whisper_en")
            self.assertEqual(cfg["audio_frontend"], "float64_downmix")
            cuda_cfg = settings({"device": "cuda:0"}, family)
            self.assertEqual(cuda_cfg["dtype"], "float16")
            with self.assertRaises(ValueError):
                settings({"language": "zh"}, family)
            with self.assertRaises(ValueError):
                settings({"device": "cpu", "dtype": "float16"}, family)
            with self.assertRaises(ValueError):
                settings({"return_timestamps": True}, family)

        for family in ("whisper_wer_hf_v3", "whisper_dwer_hf_v3"):
            cfg = settings({}, family)
            self.assertEqual(cfg["backend_kind"], "hf")
            self.assertEqual(cfg["device"], "cpu")
            self.assertEqual(cfg["dtype"], "float32")
            self.assertEqual(cfg["language"], "english")
            self.assertEqual(cfg["beam_size"], 5)
            self.assertTrue(cfg["return_timestamps"])
            self.assertFalse(cfg["condition_on_prev_tokens"])
            self.assertEqual(cfg["temperature"], DEFAULT_HF_TEMPERATURES)
            self.assertEqual(cfg["compression_ratio_threshold"], 2.4)
            self.assertEqual(cfg["logprob_threshold"], -1.0)
            self.assertEqual(cfg["no_speech_threshold"], 0.6)
            self.assertEqual(cfg["normalizer"], "whisper_en_hf")
            self.assertEqual(cfg["audio_frontend"], "strict_float32")
            cuda_cfg = settings({"device": "cuda:1"}, family)
            self.assertEqual(cuda_cfg["dtype"], "float16")
            with self.assertRaises(ValueError):
                settings({"hallucination_silence_threshold": 2.0}, family)
            with self.assertRaises(ValueError):
                settings({"language": "french", "normalizer": "whisper_en_hf"}, family)
            with self.assertRaises(ValueError):
                settings({"temperature": []}, family)
            with self.assertRaises(ValueError):
                settings({"no_speech_threshold": 1.5}, family)

    @unittest.skipUnless(importlib.util.find_spec("kaldialign"), "kaldialign optional dependency")
    def test_hf_normalizer_scoring_and_compare_recognition_compatibility(self):
        word = score_text(
            "The colour.",
            "the color",
            normalizer="whisper_en_hf",
            tokenizer=_DummyTokenizer(),
        )
        self.assertEqual(word["status"], "ok")
        self.assertEqual(word["N"], 2)
        self.assertEqual(word["errors"], 0)
        self.assertEqual(word["value"], 0.0)

        empty = score_text(
            "",
            "extra words",
            normalizer="whisper_en_hf",
            tokenizer=_DummyTokenizer(),
        )
        self.assertEqual(empty["status"], "undefined_reference")
        self.assertEqual(empty["N"], 0)
        self.assertEqual(empty["I"], 2)
        self.assertIsNone(empty["value"])

        spec = get_metric("whisper_wer_en_openai")
        raw = {
            "status": word["status"],
            "values": {"wer": word["value"]},
            "protocol": {"family": "whisper_wer_en_openai", "normalization": "whisper_en"},
            "backend": {"openai-whisper": "20250625"},
            "details": {
                "reference_text": "The colour.",
                "hypothesis_text": "the color",
                "word": word,
                "reference_fingerprint": {"word": word["reference_fingerprint"]},
                "N": word["N"],
                "S": word["S"],
                "D": word["D"],
                "I": word["I"],
                "errors": word["errors"],
            },
        }
        selected = select(raw, spec)
        self.assertEqual(selected["scoring_unit"], "word")
        self.assertEqual(selected["N"], 2)
        comparison = compare_recognition(
            {"sys_a": [{"id": "utt1", "result": selected}]},
            expected_ids=["utt1"],
        )
        self.assertTrue(comparison["full_corpus_comparable"])
        self.assertEqual(comparison["systems"]["sys_a"]["value"], 0.0)

    @unittest.skipUnless(
        all(importlib.util.find_spec(p) for p in ("espnet2", "whisper", "Levenshtein")),
        "Optional OpenAI Whisper + ESPnet cleaners",
    )
    def test_openai_whisper_en_normalizer_matches_textcleaner(self):
        word = score_text("It's colour twenty-one.", "it is color 21", normalizer="whisper_en")
        self.assertEqual(word["errors"], 0)
        self.assertEqual(word["N"], 4)

    def test_legacy_whisper_select_remains_unchanged(self):
        spec = get_metric("whisper_wer")
        raw = {
            "status": "ok",
            "values": {"wer": 25.0},
            "details": {"N": 4, "S": 1, "D": 0, "I": 0, "errors": 1},
        }
        selected = select(raw, spec)
        self.assertEqual(selected["value"], 25.0)
        self.assertEqual(selected["N"], 4)
        self.assertNotIn("scoring_unit", selected)

    def test_new_families_registered_and_lockable(self):
        for name in (
            "whisper_wer_en_openai",
            "whisper_dwer_en_openai",
            "whisper_wer_hf_v3",
            "whisper_dwer_hf_v3",
            "speaker_similarity_unispeech_wavlm",
        ):
            spec = get_metric(name)
            self.assertEqual(spec["family"], name)

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pt = root / "large-v3.pt"
            pt.write_bytes(b"whisper-ckpt")
            wavlm = root / "WavLM-Large.pt"
            wavlm.write_bytes(b"wavlm-ssl")
            ecapa = root / "wavlm_large_finetune.pth"
            ecapa.write_bytes(b"unispeech-ecapa")
            hf_dir = root / "whisper_hf"
            hf_dir.mkdir()
            (hf_dir / "config.json").write_text('{"model_type": "whisper"}', encoding="utf-8")

            lock = create_deployment(
                {
                    "whisper_wer_en_openai": {
                        "checkpoint": str(pt),
                        "trusted_checkpoint": True,
                        "device": "cpu",
                    },
                    "whisper_wer_hf_v3": {
                        "model_dir": str(hf_dir),
                        "trusted_checkpoint": True,
                        "device": "cpu",
                    },
                    "speaker_similarity_unispeech_wavlm": {
                        "ssl_checkpoint": str(wavlm),
                        "checkpoint": str(ecapa),
                        "trusted_checkpoint": True,
                        "device": "cpu",
                    },
                }
            )
            self.assertEqual(verify_deployment(lock)["status"], "ok")
            self.assertEqual(
                set(lock["configs"]["speaker_similarity_unispeech_wavlm"]["expected_hashes"]),
                {"checkpoint", "ssl_checkpoint"},
            )


class UniSpeechSpeakerModelTests(unittest.TestCase):
    @unittest.skipUnless(importlib.util.find_spec("torch"), "torch optional dependency")
    def test_ecapa_tdnn_small_forward_and_identity(self):
        import torch
        import torch.nn as nn
        from speech_eval.unispeech_sv import UniSpeechWavLMEcapa

        class _FakeUpstream(nn.Module):
            def __init__(self):
                super().__init__()
                self.proj = nn.Linear(1, 1)

            def forward(self, wavs):
                frames = max(10, len(wavs[0]) // 320)
                bsz = len(wavs)
                # Return 3 deterministic hidden-state layers of dim 1024.
                base = torch.stack([w[: frames * 320].view(frames, 320).mean(-1) for w in wavs])
                layer = base.unsqueeze(-1).expand(bsz, frames, 1024).contiguous()
                return {"hidden_states": [layer, layer * 0.5, layer * 0.25]}

        model = UniSpeechWavLMEcapa(_FakeUpstream(), feat_dim=1024, channels=512, emb_dim=256)
        model.eval()
        x = torch.randn(1, 16000)
        with torch.no_grad():
            emb1 = model(x)
            emb2 = model(x)
        self.assertEqual(tuple(emb1.shape), (1, 256))
        sim = torch.cosine_similarity(emb1, emb2, dim=-1).item()
        self.assertAlmostEqual(sim, 1.0, places=5)

    @unittest.skipUnless(importlib.util.find_spec("torch"), "torch optional dependency")
    def test_openai_loader_keeps_layernorm_fp32_under_cuda_fp16(self):
        import torch
        import torch.nn as nn
        from speech_eval.whisper_asr import _load_openai_whisper

        class _FakeLN(nn.LayerNorm):
            pass

        class _FakeModel(nn.Module):
            def __init__(self):
                super().__init__()
                self.lin = nn.Linear(4, 4)
                self.ln = _FakeLN(4)

            def to(self, device):
                # Keep on CPU in unit tests while recording the requested target device.
                self.requested_device = device
                return self

        fake_whisper = type(
            "FakeWhisper",
            (),
            {
                "load_model": staticmethod(lambda ckpt, device="cpu": _FakeModel()),
                "model": type("M", (), {"LayerNorm": _FakeLN}),
            },
        )
        with patch.dict("sys.modules", {"whisper": fake_whisper}):
            model = _load_openai_whisper("dummy.pt", device="cuda:0", dtype="float16")
        self.assertEqual(model.lin.weight.dtype, torch.float16)
        self.assertEqual(model.ln.weight.dtype, torch.float32)
        self.assertEqual(model.requested_device, "cuda:0")


if __name__ == "__main__":
    unittest.main()
