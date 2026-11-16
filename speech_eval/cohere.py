"""Offline Cohere Transcribe ASR through native Transformers (no remote code).

The existing subprocess dispatcher supplies an independent Python environment.
This module has no import-time dependency on Torch or Transformers, and never
changes Whisper's recognizer, normalization, or deployment requirements.
"""

from importlib.metadata import version
import hashlib
import math
from pathlib import Path


MODEL_ID = "CohereLabs/cohere-transcribe-03-2026"
SOURCE = "https://huggingface.co/CohereLabs/cohere-transcribe-03-2026"
LANGUAGES = {"ar", "de", "el", "en", "es", "fr", "it", "ja", "ko", "nl", "pl", "pt", "vi", "zh"}
FAMILIES = {"cohere_wer", "cohere_dwer"}


def _integer(value, name, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer from {minimum} to {maximum}")
    return value


def settings(config):
    """Validate a small explicit decoding contract before importing heavy libraries."""
    known = {
        "model_dir",
        "python",
        "timeout",
        "threads",
        "device",
        "expected_hashes",
        "trusted_checkpoint",
        "dtype",
        "language",
        "punctuation",
        "beam_size",
        "max_new_tokens",
        "max_audio_seconds",
        "chunk_batch_size",
        "worker_deployment",
        "tokenizer_file",
    }
    unknown = set(config) - known
    if unknown:
        raise ValueError(f"Unsupported Cohere configuration keys: {sorted(unknown)}")
    device = config.get("device", "cpu")
    if not isinstance(device, str) or not (
        device == "cpu" or (device.startswith("cuda:") and device[5:].isdigit())
    ):
        raise ValueError("device must be cpu or an explicit cuda:N")
    dtype = config.get("dtype", "float32" if device == "cpu" else "bfloat16")
    if dtype not in ("float32", "bfloat16") or (device == "cpu" and dtype != "float32"):
        raise ValueError("Cohere profile supports CPU float32 or CUDA float32/bfloat16")
    language = config.get("language", "en")
    if not isinstance(language, str) or language not in LANGUAGES:
        raise ValueError(f"Explicit supported language code required: {sorted(LANGUAGES)}")
    punctuation = config.get("punctuation", True)
    if not isinstance(punctuation, bool):
        raise ValueError("punctuation must be a boolean")
    maximum = config.get("max_audio_seconds", 600.0)
    if (
        isinstance(maximum, bool)
        or not isinstance(maximum, (int, float))
        or not math.isfinite(maximum)
        or maximum < 0.1
    ):
        raise ValueError("max_audio_seconds must be finite and at least 0.1")
    return {
        "device": device,
        "dtype": dtype,
        "language": language,
        "punctuation": punctuation,
        "beam_size": _integer(config.get("beam_size", 1), "beam_size", 1, 8),
        "max_new_tokens": _integer(config.get("max_new_tokens", 256), "max_new_tokens", 1, 4096),
        "chunk_batch_size": _integer(config.get("chunk_batch_size", 1), "chunk_batch_size", 1, 32),
        "threads": _integer(config.get("threads", 2), "threads", 1, 64),
        "max_audio_seconds": float(maximum),
    }


def read_audio(path, *, maximum=600.0):
    """Keep real silence for hallucination evaluation; do not add a hidden VAD."""
    import numpy as np
    import soundfile as sf
    import soxr

    path = Path(path).resolve(strict=True)
    # Check duration before allocating an arbitrarily long decoded waveform.
    info = sf.info(path)
    if info.channels != 1 or info.frames <= 0 or info.samplerate <= 0:
        raise ValueError("Cohere ASR requires a nonempty mono audio file")
    duration = info.frames / info.samplerate
    if not 0.1 <= duration <= maximum:
        raise ValueError(f"Cohere ASR requires audio between 0.1 and {maximum} seconds")
    audio, rate = sf.read(path, dtype="float32")
    if audio.ndim != 1 or not np.isfinite(audio).all():
        raise ValueError("Cohere ASR requires finite mono audio; downmix explicitly")
    exact_zero = not np.any(audio)
    if rate != 16000:
        audio = soxr.resample(audio, rate, 16000, quality="HQ")
    return audio, {"sample_rate": rate, "seconds": duration, "exact_zero_waveform": exact_zero}


def compare_text(reference_text, hypothesis_text):
    """Use the existing authoritative scorer with generic, explicit normalization."""
    from .registry import text_metric

    if not isinstance(reference_text, str) or not isinstance(hypothesis_text, str):
        raise TypeError("ASR transcripts must be strings; an empty reference is allowed")
    counts = {}
    for unit, metric in (("word", "wer"), ("char", "cer")):
        result = text_metric(metric=metric, reference=reference_text, hypothesis=hypothesis_text)
        counts[unit] = {k: result[k] for k in ("N", "S", "D", "I", "errors", "value", "status")}
    return counts


def generation_health(sequences, prompt_length, eos_token_ids):
    """Check each chunk's generated suffix, never an EOS occurring in its prompt."""
    if isinstance(eos_token_ids, int):
        eos_token_ids = [eos_token_ids]
    if not eos_token_ids or any(not isinstance(x, int) for x in eos_token_ids):
        raise ValueError("The checkpoint must declare usable EOS token IDs")
    eos = set(eos_token_ids)
    lengths, missing = [], []
    for i, sequence in enumerate(sequences):
        suffix = list(sequence)[prompt_length:]
        stop = next((j for j, token in enumerate(suffix) if int(token) in eos), None)
        lengths.append(len(suffix) if stop is None else stop + 1)
        if stop is None:
            missing.append(i)
    return {
        "complete": not missing,
        "missing_eos_chunks": missing,
        "generated_tokens_per_chunk": lengths,
    }


def _reassemble(processor, padded, chunks, language):
    """Preserve native transcript text; guard only the long-chunk empty-list bug."""
    raw = processor.tokenizer.decode(padded, skip_special_tokens=True)
    raw = [raw] if isinstance(raw, str) else raw
    if (
        not isinstance(raw, list)
        or len(raw) != len(chunks)
        or not all(isinstance(t, str) for t in raw)
    ):
        raise RuntimeError("Unexpected native tokenizer decode result")
    if any(index is not None for _, index in chunks) and all(not text.strip() for text in raw):
        return "", True
    decoded = processor.decode(
        padded, skip_special_tokens=True, audio_chunk_index=chunks, language=language
    )
    if not isinstance(decoded, list) or len(decoded) != 1 or not isinstance(decoded[0], str):
        raise RuntimeError("Native processor failed to reassemble exactly one transcript")
    return decoded[0], False


def _decode(audio, processor, model, cfg):
    import torch

    inputs = processor(
        audio=audio,
        sampling_rate=16000,
        return_tensors="pt",
        language=cfg["language"],
        punctuation=cfg["punctuation"],
    )
    chunks = inputs.get("audio_chunk_index")
    chunk_count = int(inputs["input_features"].shape[0])
    if chunks is None or len(chunks) != chunk_count:
        raise RuntimeError("Native processor did not return a complete audio_chunk_index")
    if any(int(sample) != 0 for sample, _ in chunks):
        raise RuntimeError("Unexpected processor sample mapping for one recording")
    prompt_length = int(inputs["decoder_input_ids"].shape[1])
    # Send only tensors to the model; keep chunk metadata on CPU for reassembly.
    results = []
    with torch.inference_mode():
        for start in range(0, chunk_count, cfg["chunk_batch_size"]):
            stop = min(start + cfg["chunk_batch_size"], chunk_count)
            batch = {}
            for key, value in inputs.items():
                if not isinstance(value, torch.Tensor):
                    continue
                value = value[start:stop]
                batch[key] = value.to(
                    device=model.device,
                    dtype=model.dtype if value.is_floating_point() else value.dtype,
                )
            output = model.generate(
                **batch,
                num_beams=cfg["beam_size"],
                do_sample=False,
                max_new_tokens=cfg["max_new_tokens"],
                return_dict_in_generate=False,
                forced_eos_token_id=None,
            )
            results.extend(output.detach().cpu().tolist())
    eos_ids = model.generation_config.eos_token_id
    if eos_ids is None:
        eos_ids = processor.tokenizer.eos_token_id
    health = generation_health(results, prompt_length, eos_ids)
    health.update(chunks=chunk_count, audio_chunk_index=[list(x) for x in chunks])
    pad = model.generation_config.pad_token_id
    if pad is None:
        pad = processor.tokenizer.pad_token_id
    if pad is None:
        raise ValueError("The checkpoint must declare a padding token")
    padded = torch.tensor([r + [pad] * (max(map(len, results)) - len(r)) for r in results])
    # Transformers 5.4's long-audio reassembler indexes non_empty[0]. Avoid its
    # empty-list error only when every decoded chunk is empty; no text is removed.
    text, guarded = _reassemble(processor, padded, chunks, cfg["language"])
    health["empty_chunk_reassembly_guard"] = guarded
    return text, health


def score(request):
    """Private model-worker entry; returns both word and character error heads."""
    family = request["family"]
    if family not in FAMILIES:
        raise ValueError(f"Unsupported Cohere model family: {family}")
    config = dict(request.get("config") or {})
    cfg = settings(config)
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
                "reason": "Cohere worker deployment file no longer matches its parent pin",
            }
        verification = verify_deployment(config["worker_deployment"], families=[family])
        if verification["status"] != "ok":
            return {
                "status": "deployment_mismatch",
                "values": {},
                "reason": "Cohere worker deployment validation failed",
                "verification": verification,
            }
    import torch
    from packaging.version import Version
    from .model_worker import artifact, require

    torch.set_num_threads(cfg["threads"])
    if Version(version("transformers")) < Version("5.4.0"):
        raise ImportError(
            "Native Cohere ASR requires transformers>=5.4.0 in a separate worker environment"
        )
    from transformers import AutoProcessor, CohereAsrForConditionalGeneration

    if cfg["device"].startswith("cuda:"):
        if not torch.cuda.is_available():
            raise ValueError("CUDA requested but unavailable")
        if cfg["dtype"] == "bfloat16" and not torch.cuda.is_bf16_supported():
            raise ValueError("CUDA device does not support the requested bfloat16 precision")
    path = require(config, "model_dir")
    if not Path(path).is_dir():
        raise ValueError("model_dir must be a local model directory")
    hypothesis = request["hypothesis"]
    reference = request.get("reference")
    if family == "cohere_wer" and not isinstance(reference, str):
        raise ValueError(
            "Cohere WER/CER requires ground-truth reference text (including empty text)"
        )
    if family == "cohere_dwer" and not isinstance(reference, (str, Path)):
        raise ValueError("Cohere dWER/dCER requires a clean-reference audio path")
    wave, hyp_info = read_audio(hypothesis, maximum=cfg["max_audio_seconds"])
    reference_wave, ref_info = (None, None)
    if family == "cohere_dwer":
        reference_wave, ref_info = read_audio(reference, maximum=cfg["max_audio_seconds"])
    provenance = {"hypothesis": artifact(hypothesis), "model_dir": artifact(path)}
    if config.get("tokenizer_file"):
        tokenizer_path = Path(require(config, "tokenizer_file"))
        if tokenizer_path.resolve() != (Path(path) / "tokenizer.model").resolve():
            raise ValueError("tokenizer_file must identify model_dir/tokenizer.model")
        provenance["tokenizer_file"] = artifact(tokenizer_path)
    elif (Path(path) / "tokenizer.model").is_file():
        provenance["tokenizer_file"] = artifact(Path(path) / "tokenizer.model")
    if family == "cohere_dwer":
        provenance["reference"] = artifact(reference)
    for key, expected in config.get("expected_hashes", {}).items():
        if key == "worker_deployment":
            continue
        if key not in provenance or provenance[key]["sha256"] != expected:
            raise ValueError(f"Artifact hash mismatch: {key}")
    dtype = getattr(torch, cfg["dtype"])
    processor = AutoProcessor.from_pretrained(path, local_files_only=True, trust_remote_code=False)
    model = (
        CohereAsrForConditionalGeneration.from_pretrained(
            path,
            local_files_only=True,
            trust_remote_code=False,
            use_safetensors=True,
            dtype=dtype,
        )
        .to(cfg["device"])
        .eval()
    )
    if model.config.model_type != "cohere_asr":
        raise ValueError("Expected native cohere_asr model configuration")
    hyp_text, hyp_decode = _decode(wave, processor, model, cfg)
    ref_decode = None
    if family == "cohere_dwer":
        ref_text, ref_decode = _decode(reference_wave, processor, model, cfg)
    else:
        ref_text = reference
    extractor = processor.feature_extractor
    protocol = {
        "family": family,
        "profile": "cohere_transcribe_native_v1",
        "source": SOURCE,
        "model_id": MODEL_ID,
        "scoring_sample_rate": 16000,
        "channel_policy": "strict_mono",
        "resampler": "soxr_HQ",
        "gain_normalization": "none",
        "silence_policy": "decode_no_vad",
        "normalization": "nfkc-casefold-v1",
        "number_normalization": "no_verbalization",
        "word_tokenization": "whitespace_no_implicit_language_segmentation",
        "character_tokenization": "normalized_unicode_letters_marks_numbers_without_spaces",
        "language": cfg["language"],
        "punctuation": cfg["punctuation"],
        "dtype": cfg["dtype"],
        "beam_size": cfg["beam_size"],
        "do_sample": False,
        "max_new_tokens": cfg["max_new_tokens"],
        "forced_eos_token_id": None,
        "truncation_policy": "reject_missing_generated_eos",
        "minimum_seconds": 0.1,
        "max_audio_seconds": cfg["max_audio_seconds"],
        "chunk_batch_size": cfg["chunk_batch_size"],
        "chunking": "native_processor_energy_boundaries",
        "max_audio_clip_s": extractor.max_audio_clip_s,
        "boundary_search_seconds": extractor.overlap_chunk_second,
        "min_energy_window_samples": extractor.min_energy_window_samples,
        "dither": extractor.dither,
        "download_policy": "offline",
        "trust_remote_code": False,
        "reference_mode": "clean_reference_asr" if family == "cohere_dwer" else "ground_truth_text",
        "aggregation": "micro_errors_over_reference_units",
        "artifact_hashes": {
            key: provenance[key]["sha256"]
            for key in ("model_dir", "tokenizer_file")
            if key in provenance
        },
    }
    backend = {
        p: version(p)
        for p in (
            "torch",
            "transformers",
            "tokenizers",
            "librosa",
            "numpy",
            "soundfile",
            "soxr",
            "meeteval",
            "kaldialign",
        )
    }
    details = {
        "hypothesis_text": hyp_text,
        "reference_text": ref_text,
        "hypothesis_audio": hyp_info,
        "reference_audio": ref_info,
        "hypothesis_decode": hyp_decode,
        "reference_decode": ref_decode,
    }
    base = {"protocol": protocol, "backend": backend, "provenance": provenance, "details": details}
    if not hyp_decode["complete"] or (ref_decode is not None and not ref_decode["complete"]):
        return {
            **base,
            "status": "generation_truncated",
            "values": {},
            "reason": "A chunk has no generated EOS; partial transcription is not scored. Increase max_new_tokens.",
        }
    counts = compare_text(ref_text, hyp_text)
    details.update(counts)
    return {
        **base,
        "status": "ok" if counts["word"]["N"] else "undefined_reference",
        "values": {"wer": counts["word"]["value"], "cer": counts["char"]["value"]},
    }
