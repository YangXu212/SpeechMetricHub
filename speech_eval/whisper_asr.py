"""Explicit OpenAI Whisper and upgraded Hugging Face Whisper ASR profiles.

Legacy ``whisper_wer`` and ``whisper_dwer`` remain untouched in ``model_worker.py``
for historical lock compatibility. New experiments should prefer:

- ``whisper_wer_en_openai`` / ``whisper_dwer_en_openai``: Official OpenAI Whisper
  ``large-v3`` (``beam_size=5``, ``hallucination_silence_threshold=2.0``) with
  ESPnet/OpenAI ``whisper_en`` normalization and Levenshtein opcodes. This matches
  the standard OpenAI Whisper evaluation pipeline used in enhancement/TSE papers.
- ``whisper_wer_hf_v3`` / ``whisper_dwer_hf_v3``: Upgraded Hugging Face
  Transformers Whisper profile with ``return_timestamps=True``, temperature
  fallback, ``condition_on_prev_tokens=False``, native ``>30s`` long-form
  decoding, and full Whisper English spelling normalization.
"""

from importlib.metadata import PackageNotFoundError, version
import hashlib
import json
import math
from pathlib import Path


OPENAI_FAMILIES = ("whisper_wer_en_openai", "whisper_dwer_en_openai")
HF_FAMILIES = ("whisper_wer_hf_v3", "whisper_dwer_hf_v3")
FAMILIES = set(OPENAI_FAMILIES) | set(HF_FAMILIES)
REFERENCE_AUDIO_FAMILIES = {"whisper_dwer_en_openai", "whisper_dwer_hf_v3"}

OPENAI_SOURCE = "https://github.com/openai/whisper"
HF_SOURCE = "https://huggingface.co/openai/whisper-large-v3"
DEFAULT_HF_TEMPERATURES = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]


def _integer(value, name, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer from {minimum} to {maximum}")
    return value


def _optional_float(value, name, *, minimum=None, maximum=None):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number or null")
    value = float(value)
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must be at most {maximum}")
    return value


def _temperatures(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        items = [value]
    elif isinstance(value, (list, tuple)) and value:
        items = list(value)
    else:
        raise ValueError("temperature must be a finite float or a nonempty sequence of floats")
    result = []
    for item in items:
        val = _optional_float(item, "temperature", minimum=0.0, maximum=2.0)
        if val is None:
            raise ValueError("temperature entries cannot be null")
        result.append(val)
    return result


def settings(config, family="whisper_wer_en_openai"):
    """Validate explicit Whisper decoding configuration before heavy imports."""
    if family not in FAMILIES:
        raise ValueError(f"Unsupported Whisper model family: {family}")
    is_openai = family in OPENAI_FAMILIES
    known = {
        "python",
        "timeout",
        "threads",
        "device",
        "expected_hashes",
        "trusted_checkpoint",
        "dtype",
        "language",
        "beam_size",
        "max_audio_seconds",
        "normalizer",
        "audio_frontend",
        "worker_deployment",
    }
    if is_openai:
        known |= {"checkpoint", "hallucination_silence_threshold"}
    else:
        known |= {
            "model_dir",
            "return_timestamps",
            "condition_on_prev_tokens",
            "temperature",
            "compression_ratio_threshold",
            "logprob_threshold",
            "no_speech_threshold",
        }
    unknown = set(config) - known
    if unknown:
        raise ValueError(f"Unsupported Whisper configuration keys: {sorted(unknown)}")
    device = config.get("device", "cpu")
    if not isinstance(device, str) or not (
        device == "cpu" or (device.startswith("cuda:") and device[5:].isdigit())
    ):
        raise ValueError("device must be cpu or an explicit cuda:N")
    dtype = config.get("dtype", "float32" if device == "cpu" else "float16")
    if dtype not in ("float32", "float16") or (device == "cpu" and dtype != "float32"):
        raise ValueError("Whisper profile supports CPU float32 or CUDA float32/float16")
    maximum = _optional_float(config.get("max_audio_seconds", 600.0), "max_audio_seconds")
    if maximum is None or maximum < 0.1:
        raise ValueError("max_audio_seconds must be finite and at least 0.1")
    beam_size = _integer(config.get("beam_size", 5), "beam_size", 1, 16)
    threads = _integer(config.get("threads", 2), "threads", 1, 64)
    frontend = config.get("audio_frontend", "float64_downmix" if is_openai else "strict_float32")
    if frontend not in ("strict_float32", "float64_downmix"):
        raise ValueError("audio_frontend must be strict_float32 or float64_downmix")

    if is_openai:
        language = config.get("language", "en")
        if language != "en":
            raise ValueError(f"{family} requires language='en'")
        normalizer = config.get("normalizer", "whisper_en")
        if normalizer not in ("whisper_en", "whisper_basic", "nfkc-casefold-v1"):
            raise ValueError(
                "Unknown normalizer; choose whisper_en, whisper_basic or nfkc-casefold-v1"
            )
        hst = _optional_float(
            config.get("hallucination_silence_threshold", 2.0),
            "hallucination_silence_threshold",
            minimum=0.0,
        )
        return {
            "backend_kind": "openai",
            "device": device,
            "dtype": dtype,
            "language": language,
            "beam_size": beam_size,
            "hallucination_silence_threshold": hst,
            "threads": threads,
            "max_audio_seconds": maximum,
            "normalizer": normalizer,
            "audio_frontend": frontend,
        }

    language = config.get("language", "english")
    if not isinstance(language, str) or not language.strip():
        raise ValueError("language must be a nonempty string")
    normalizer = config.get("normalizer", "whisper_en_hf")
    if normalizer not in ("whisper_en_hf", "whisper_en", "whisper_basic", "nfkc-casefold-v1"):
        raise ValueError(
            "Unknown normalizer; choose whisper_en_hf, whisper_en, whisper_basic or nfkc-casefold-v1"
        )
    if normalizer in ("whisper_en_hf", "whisper_en") and language != "english":
        raise ValueError(f"normalizer={normalizer} requires language='english'")
    return_timestamps = config.get("return_timestamps", True)
    if not isinstance(return_timestamps, bool):
        raise ValueError("return_timestamps must be a boolean")
    condition_on_prev = config.get("condition_on_prev_tokens", False)
    if not isinstance(condition_on_prev, bool):
        raise ValueError("condition_on_prev_tokens must be a boolean")
    return {
        "backend_kind": "hf",
        "device": device,
        "dtype": dtype,
        "language": language,
        "beam_size": beam_size,
        "return_timestamps": return_timestamps,
        "condition_on_prev_tokens": condition_on_prev,
        "temperature": _temperatures(config.get("temperature", DEFAULT_HF_TEMPERATURES)),
        "compression_ratio_threshold": _optional_float(
            config.get("compression_ratio_threshold", 2.4),
            "compression_ratio_threshold",
            minimum=0.0,
        ),
        "logprob_threshold": _optional_float(
            config.get("logprob_threshold", -1.0), "logprob_threshold"
        ),
        "no_speech_threshold": _optional_float(
            config.get("no_speech_threshold", 0.6),
            "no_speech_threshold",
            minimum=0.0,
            maximum=1.0,
        ),
        "threads": threads,
        "max_audio_seconds": maximum,
        "normalizer": normalizer,
        "audio_frontend": frontend,
    }


def _kaldialign_counts(ref_tokens, hyp_tokens):
    n = len(ref_tokens)
    if not n:
        ins = len(hyp_tokens)
        return {
            "N": 0,
            "S": 0,
            "D": 0,
            "I": ins,
            "errors": ins,
            "value": None,
            "status": "undefined_reference",
        }
    import kaldialign

    counts = kaldialign.edit_distance(ref_tokens, hyp_tokens)
    sub, dele, ins = int(counts["sub"]), int(counts["del"]), int(counts["ins"])
    errors = sub + dele + ins
    if errors != int(counts["total"]):
        raise RuntimeError("kaldialign edit totals disagree with S + D + I")
    return {
        "N": n,
        "S": sub,
        "D": dele,
        "I": ins,
        "errors": errors,
        "value": 100 * errors / n,
        "status": "ok",
    }


def score_text(reference_text, hypothesis_text, *, normalizer, tokenizer=None):
    """Score normalized Whisper transcripts and return word counts + fingerprint."""
    if not isinstance(reference_text, str) or not isinstance(hypothesis_text, str):
        raise TypeError("ASR transcripts must be strings; an empty reference is allowed")
    if normalizer in ("whisper_en", "whisper_basic", "nfkc-casefold-v1"):
        from .cohere import compare_text

        return compare_text(reference_text, hypothesis_text, normalizer=normalizer)["word"]
    if normalizer == "whisper_en_hf":
        if tokenizer is None or not hasattr(tokenizer, "normalize"):
            raise ValueError(
                "whisper_en_hf normalizer requires a Whisper tokenizer with normalize()"
            )
        ref_norm = tokenizer.normalize(reference_text)
        hyp_norm = tokenizer.normalize(hypothesis_text)
        ref_tokens, hyp_tokens = ref_norm.split(), hyp_norm.split()
        word = _kaldialign_counts(ref_tokens, hyp_tokens)
        word.update(
            normalized_reference_text=ref_norm,
            normalized_hypothesis_text=hyp_norm,
            reference_tokens=ref_tokens,
            hypothesis_tokens=hyp_tokens,
            reference_fingerprint=hashlib.sha256(
                json.dumps(ref_tokens, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
        )
        return word
    raise ValueError(f"Unsupported normalizer: {normalizer}")


def _load_openai_whisper(checkpoint, *, device, dtype):
    import whisper

    load_device = "cpu" if device == "cpu" or dtype == "float16" else device
    model = whisper.load_model(checkpoint, device=load_device)
    if device != "cpu" and dtype == "float16":
        model.half()
        for module in model.modules():
            if isinstance(module, whisper.model.LayerNorm):
                module.float()
        model = model.to(device)
    return model.eval()


def _transcribe_openai(model, wave, cfg):
    import torch

    use_fp16 = cfg["device"] != "cpu" and cfg["dtype"] == "float16"
    kwargs = {
        "task": "transcribe",
        "language": cfg["language"],
        "beam_size": cfg["beam_size"],
        "fp16": use_fp16,
        "verbose": None,
    }
    if cfg["hallucination_silence_threshold"] is not None:
        kwargs["hallucination_silence_threshold"] = cfg["hallucination_silence_threshold"]
    with torch.no_grad():
        result = model.transcribe(wave, **kwargs)
    return str(result.get("text", "")).strip()


def _transcribe_hf(model, processor, wave, cfg):
    import torch

    dtype = getattr(torch, cfg["dtype"])
    is_long = len(wave) > 30 * 16000
    if is_long:
        inputs = processor(
            wave,
            sampling_rate=16000,
            return_tensors="pt",
            truncation=False,
            padding="longest",
            return_attention_mask=True,
        )
    else:
        inputs = processor(
            wave,
            sampling_rate=16000,
            return_tensors="pt",
            return_attention_mask=True,
        )
    gen_kwargs = {
        "attention_mask": inputs.attention_mask.to(cfg["device"]),
        "language": cfg["language"],
        "task": "transcribe",
        "num_beams": cfg["beam_size"],
        "return_timestamps": cfg["return_timestamps"],
        "condition_on_prev_tokens": cfg["condition_on_prev_tokens"],
        "temperature": tuple(cfg["temperature"]),
    }
    if cfg["temperature"] == [0.0]:
        gen_kwargs["do_sample"] = False
    if cfg["compression_ratio_threshold"] is not None:
        gen_kwargs["compression_ratio_threshold"] = cfg["compression_ratio_threshold"]
    if cfg["logprob_threshold"] is not None:
        gen_kwargs["logprob_threshold"] = cfg["logprob_threshold"]
    if cfg["no_speech_threshold"] is not None:
        gen_kwargs["no_speech_threshold"] = cfg["no_speech_threshold"]
    with torch.inference_mode():
        pred = model.generate(
            inputs.input_features.to(cfg["device"], dtype=dtype),
            **gen_kwargs,
        )
    return processor.batch_decode(pred, skip_special_tokens=True)[0].strip()


def _pkg_versions(names):
    info = {}
    for name in names:
        try:
            info[name] = version(name)
        except PackageNotFoundError:
            pass
    return info


def score(request):
    """Private model-worker entry for OpenAI Whisper and upgraded HF Whisper profiles."""
    family = request["family"]
    if family not in FAMILIES:
        raise ValueError(f"Unsupported Whisper model family: {family}")
    config = dict(request.get("config") or {})
    cfg = settings(config, family)
    audio_reference = family in REFERENCE_AUDIO_FAMILIES
    if config.get("worker_deployment"):
        from .deployment import verify_deployment

        pinned = config.get("expected_hashes", {}).get("worker_deployment")
        if (
            pinned
            and hashlib.sha256(Path(config["worker_deployment"]).read_bytes()).hexdigest() != pinned
        ):
            return {
                "status": "deployment_mismatch",
                "values": {},
                "reason": "Whisper worker deployment file no longer matches its parent pin",
            }
        verification = verify_deployment(config["worker_deployment"], families=[family])
        if verification["status"] != "ok":
            return {
                "status": "deployment_mismatch",
                "values": {},
                "reason": "Whisper worker deployment validation failed",
                "verification": verification,
            }

    import torch
    from .cohere import read_audio
    from .model_worker import artifact, require

    torch.set_num_threads(cfg["threads"])
    if cfg["device"].startswith("cuda:") and not torch.cuda.is_available():
        raise ValueError("CUDA requested but unavailable")

    hypothesis = request["hypothesis"]
    reference = request.get("reference")
    if not audio_reference and not isinstance(reference, str):
        raise ValueError("Whisper WER requires ground-truth reference text (including empty text)")
    if audio_reference and not isinstance(reference, (str, Path)):
        raise ValueError("Whisper dWER requires a clean-reference audio path")

    wave, hyp_info = read_audio(
        hypothesis, maximum=cfg["max_audio_seconds"], frontend=cfg["audio_frontend"]
    )
    ref_wave, ref_info = (None, None)
    if audio_reference:
        ref_wave, ref_info = read_audio(
            reference, maximum=cfg["max_audio_seconds"], frontend=cfg["audio_frontend"]
        )

    provenance = {"hypothesis": artifact(hypothesis)}
    if audio_reference:
        provenance["reference"] = artifact(reference)

    if cfg["backend_kind"] == "openai":
        if not config.get("trusted_checkpoint"):
            raise ValueError("Set trusted_checkpoint=true only for trusted local PyTorch artifacts")
        ckpt = require(config, "checkpoint")
        if not Path(ckpt).is_file():
            raise ValueError("checkpoint must be a local OpenAI Whisper .pt file")
        provenance["checkpoint"] = artifact(ckpt)
    else:
        model_dir = require(config, "model_dir")
        if not Path(model_dir).is_dir():
            raise ValueError("model_dir must be a local Hugging Face Whisper directory")
        provenance["model_dir"] = artifact(model_dir)

    for key, expected in config.get("expected_hashes", {}).items():
        if key == "worker_deployment":
            continue
        if key not in provenance or provenance[key]["sha256"] != expected:
            raise ValueError(f"Artifact hash mismatch: {key}")

    tokenizer = None
    if cfg["backend_kind"] == "openai":
        model = _load_openai_whisper(
            provenance["checkpoint"]["path"], device=cfg["device"], dtype=cfg["dtype"]
        )
        hyp_text = _transcribe_openai(model, wave, cfg)
        ref_text = _transcribe_openai(model, ref_wave, cfg) if audio_reference else reference
    else:
        from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

        dtype = getattr(torch, cfg["dtype"])
        processor = AutoProcessor.from_pretrained(
            provenance["model_dir"]["path"], local_files_only=True
        )
        tokenizer = processor.tokenizer
        model = (
            AutoModelForSpeechSeq2Seq.from_pretrained(
                provenance["model_dir"]["path"],
                local_files_only=True,
                torch_dtype=dtype,
            )
            .to(cfg["device"])
            .eval()
        )
        if getattr(model.generation_config, "forced_decoder_ids", None) is not None:
            model.generation_config.forced_decoder_ids = None
        hyp_text = _transcribe_hf(model, processor, wave, cfg)
        ref_text = _transcribe_hf(model, processor, ref_wave, cfg) if audio_reference else reference

    word = score_text(ref_text, hyp_text, normalizer=cfg["normalizer"], tokenizer=tokenizer)
    protocol = {
        "family": family,
        "profile": family,
        "source": OPENAI_SOURCE if cfg["backend_kind"] == "openai" else HF_SOURCE,
        "backend_kind": cfg["backend_kind"],
        "scoring_sample_rate": 16000,
        "channel_policy": (
            "float64_arithmetic_mean_channels"
            if cfg["audio_frontend"] == "float64_downmix"
            else "strict_mono"
        ),
        "resampler": "soxr_HQ",
        "gain_normalization": "none",
        "silence_policy": "decode_no_vad",
        "normalization": cfg["normalizer"],
        "word_tokenization": "whitespace_no_implicit_language_segmentation",
        "language": cfg["language"],
        "dtype": cfg["dtype"],
        "beam_size": cfg["beam_size"],
        "minimum_seconds": 0.1,
        "max_audio_seconds": cfg["max_audio_seconds"],
        "long_form_policy": (
            "openai_whisper_30s_sliding_window"
            if cfg["backend_kind"] == "openai"
            else "hf_sequential_long_form_timestamps"
        ),
        "download_policy": "offline",
        "reference_mode": "clean_reference_asr" if audio_reference else "ground_truth_text",
        "aggregation": "micro_errors_over_reference_units",
    }
    if cfg["backend_kind"] == "openai":
        protocol["hallucination_silence_threshold"] = cfg["hallucination_silence_threshold"]
        protocol["layer_norm_dtype"] = "float32"
        protocol["artifact_hashes"] = {"checkpoint": provenance["checkpoint"]["sha256"]}
    else:
        protocol.update(
            return_timestamps=cfg["return_timestamps"],
            condition_on_prev_tokens=cfg["condition_on_prev_tokens"],
            temperature=cfg["temperature"],
            compression_ratio_threshold=cfg["compression_ratio_threshold"],
            logprob_threshold=cfg["logprob_threshold"],
            no_speech_threshold=cfg["no_speech_threshold"],
            artifact_hashes={"model_dir": provenance["model_dir"]["sha256"]},
        )
    if cfg["normalizer"] in ("whisper_en", "whisper_basic"):
        protocol["normalization_source"] = "espnet2.text.cleaner.TextCleaner"
        protocol["edit_counts"] = "python_Levenshtein.opcodes_reference_span_except_insert"
    elif cfg["normalizer"] == "whisper_en_hf":
        protocol["normalization_source"] = "transformers.WhisperTokenizer.normalize"
        protocol["edit_counts"] = "kaldialign.edit_distance"

    pkgs = ["torch", "numpy", "soundfile", "soxr"]
    if cfg["backend_kind"] == "openai":
        pkgs += ["openai-whisper", "tiktoken"]
    else:
        pkgs += ["transformers", "tokenizers", "kaldialign", "meeteval"]
    if cfg["normalizer"] in ("whisper_en", "whisper_basic"):
        pkgs += ["espnet", "openai-whisper", "Levenshtein"]
    backend = _pkg_versions(dict.fromkeys(pkgs))

    details = {
        "reference_text": ref_text,
        "hypothesis_text": hyp_text,
        "hypothesis_audio": hyp_info,
        "reference_audio": ref_info,
        "word": word,
        "reference_fingerprint": {"word": word["reference_fingerprint"]},
        "normalized_reference_text": word["normalized_reference_text"],
        "normalized_hypothesis_text": word["normalized_hypothesis_text"],
        **{k: word[k] for k in ("N", "S", "D", "I", "errors")},
    }
    return {
        "status": word["status"],
        "values": {"wer": word["value"]},
        "protocol": protocol,
        "backend": backend,
        "provenance": provenance,
        "details": details,
    }
