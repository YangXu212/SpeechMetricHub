"""Offline Cohere Transcribe ASR through native Transformers (no remote code).

The existing subprocess dispatcher supplies an independent Python environment.
This module has no import-time dependency on Torch or Transformers, and never
changes Whisper's recognizer, normalization, or deployment requirements.
"""

from importlib.metadata import version
import hashlib
import json
import math
from pathlib import Path


MODEL_ID = "CohereLabs/cohere-transcribe-03-2026"
SOURCE = "https://huggingface.co/CohereLabs/cohere-transcribe-03-2026"
LANGUAGES = {"ar", "de", "el", "en", "es", "fr", "it", "ja", "ko", "nl", "pl", "pt", "vi", "zh"}
PROFILE_DEFAULTS = {
    "cohere_wer_en_whisper": {"language": "en", "normalizer": "whisper_en"},
    "cohere_dwer_en_whisper": {"language": "en", "normalizer": "whisper_en"},
    "cohere_cer_zh_basic": {"language": "zh", "normalizer": "whisper_basic"},
    "cohere_dcer_zh_basic": {"language": "zh", "normalizer": "whisper_basic"},
}
FAMILIES = {"cohere_wer", "cohere_dwer", *PROFILE_DEFAULTS}
REFERENCE_AUDIO_FAMILIES = {
    "cohere_dwer",
    "cohere_dwer_en_whisper",
    "cohere_dcer_zh_basic",
}


def _integer(value, name, minimum, maximum):
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be an integer from {minimum} to {maximum}")
    return value


def settings(config, family="cohere_wer"):
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
        "normalizer",
        "truncation_policy",
        "audio_frontend",
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
    if family not in FAMILIES:
        raise ValueError(f"Unsupported Cohere model family: {family}")
    defaults = PROFILE_DEFAULTS.get(family, {})
    language = config.get("language", defaults.get("language", "en"))
    if not isinstance(language, str) or language not in LANGUAGES:
        raise ValueError(f"Explicit supported language code required: {sorted(LANGUAGES)}")
    if defaults and language != defaults["language"]:
        raise ValueError(f"{family} requires language={defaults['language']}")
    punctuation = config.get("punctuation", not bool(defaults))
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
    normalizer = config.get("normalizer", defaults.get("normalizer", "nfkc-casefold-v1"))
    if normalizer not in ("nfkc-casefold-v1", "whisper_en", "whisper_basic"):
        raise ValueError("Unknown normalizer; choose nfkc-casefold-v1, whisper_en or whisper_basic")
    truncation = config.get("truncation_policy", "score" if defaults else "reject")
    if truncation not in ("reject", "score"):
        raise ValueError("truncation_policy must be reject or score")
    frontend = config.get("audio_frontend", "float64_downmix" if defaults else "strict_float32")
    if frontend not in ("strict_float32", "float64_downmix"):
        raise ValueError("audio_frontend must be strict_float32 or float64_downmix")
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
        "normalizer": normalizer,
        "truncation_policy": truncation,
        "audio_frontend": frontend,
    }


def read_audio(path, *, maximum=600.0, frontend="strict_float32"):
    """Keep real silence for hallucination evaluation; do not add a hidden VAD."""
    import numpy as np
    import soundfile as sf
    import soxr

    path = Path(path).resolve(strict=True)
    # Check duration before allocating an arbitrarily long decoded waveform.
    info = sf.info(path)
    if frontend not in ("strict_float32", "float64_downmix"):
        raise ValueError("Unknown audio frontend")
    if (
        (info.channels != 1 and frontend == "strict_float32")
        or info.frames <= 0
        or info.samplerate <= 0
    ):
        raise ValueError("Cohere ASR requires a nonempty mono audio file")
    duration = info.frames / info.samplerate
    if not 0.1 <= duration <= maximum:
        raise ValueError(f"Cohere ASR requires audio between 0.1 and {maximum} seconds")
    audio, rate = sf.read(path, dtype="float64" if frontend == "float64_downmix" else "float32")
    if not np.isfinite(audio).all():
        raise ValueError("Cohere ASR requires finite audio")
    if frontend == "float64_downmix" and audio.ndim == 2:
        audio = audio.mean(axis=-1)
    if audio.ndim != 1:
        raise ValueError("Cohere ASR requires finite mono audio; downmix explicitly")
    exact_zero = not np.any(audio)
    if rate != 16000:
        audio = soxr.resample(audio, rate, 16000, quality="HQ")
    if frontend == "float64_downmix":
        audio = np.ascontiguousarray(audio, dtype=np.float32)
    return audio, {"sample_rate": rate, "seconds": duration, "exact_zero_waveform": exact_zero}


def compare_text(reference_text, hypothesis_text, *, normalizer="nfkc-casefold-v1"):
    """Apply the named upstream normalizer without an implicit second cleanup."""
    from .registry import text_metric

    if not isinstance(reference_text, str) or not isinstance(hypothesis_text, str):
        raise TypeError("ASR transcripts must be strings; an empty reference is allowed")
    if normalizer == "nfkc-casefold-v1":
        from .transcription import normalize, tokenize

        ref_normalized, hyp_normalized = normalize(reference_text), normalize(hypothesis_text)
    elif normalizer in ("whisper_en", "whisper_basic"):
        from espnet2.text.cleaner import TextCleaner

        cleaner = TextCleaner(normalizer)
        ref_normalized, hyp_normalized = cleaner(reference_text), cleaner(hypothesis_text)
    else:
        raise ValueError(f"Unsupported normalizer: {normalizer}")
    counts = {}
    for unit, metric in (("word", "wer"), ("char", "cer")):
        if normalizer == "nfkc-casefold-v1":
            result = text_metric(
                metric=metric, reference=reference_text, hypothesis=hypothesis_text
            )
            ref_tokens, hyp_tokens = tokenize(reference_text, unit), tokenize(hypothesis_text, unit)
            counts[unit] = {k: result[k] for k in ("N", "S", "D", "I", "errors", "value", "status")}
        else:
            # Preserve upstream normalized strings verbatim; never apply a second
            # generic punctuation/number normalizer after the selected cleaner.
            ref_tokens, hyp_tokens = [
                text.split() if unit == "word" else [c for c in text if not c.isspace()]
                for text in (ref_normalized, hyp_normalized)
            ]
            counts[unit] = _levenshtein_counts(ref_tokens, hyp_tokens)
        counts[unit].update(
            normalized_reference_text=ref_normalized,
            normalized_hypothesis_text=hyp_normalized,
            reference_tokens=ref_tokens,
            hypothesis_tokens=hyp_tokens,
            reference_fingerprint=hashlib.sha256(
                json.dumps(ref_tokens, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            ).hexdigest(),
        )
    return counts


def _levenshtein_counts(reference_tokens, hypothesis_tokens):
    """Original Levenshtein opcode counting, including its alignment tie policy."""
    import Levenshtein

    counts = {"equal": 0, "replace": 0, "delete": 0, "insert": 0}
    for operation, ref_start, ref_end, hyp_start, hyp_end in Levenshtein.opcodes(
        reference_tokens, hypothesis_tokens
    ):
        counts[operation] += hyp_end - hyp_start if operation == "insert" else ref_end - ref_start
    if counts["equal"] + counts["replace"] + counts["delete"] != len(reference_tokens):
        raise RuntimeError("Reference opcode accounting does not cover the normalized tokens")
    if counts["equal"] + counts["replace"] + counts["insert"] != len(hypothesis_tokens):
        raise RuntimeError("Hypothesis opcode accounting does not cover the normalized tokens")
    n = len(reference_tokens)
    errors = counts["replace"] + counts["delete"] + counts["insert"]
    return {
        "N": n,
        "S": counts["replace"],
        "D": counts["delete"],
        "I": counts["insert"],
        "errors": errors,
        "value": 100 * errors / n if n else None,
        "status": "ok" if n else "undefined_reference",
    }


def finalize_score(base, *, normalizer="nfkc-casefold-v1", truncation_policy="reject"):
    """Apply the declared inclusion policy without dropping or retrying a recording."""
    if truncation_policy not in ("reject", "score"):
        raise ValueError("Unknown truncation policy")
    details = base["details"]
    hyp_decode, ref_decode = details["hypothesis_decode"], details["reference_decode"]
    generation_complete = hyp_decode["complete"] and (ref_decode is None or ref_decode["complete"])
    details["generation_complete"] = generation_complete
    if not generation_complete and truncation_policy == "reject":
        return {
            **base,
            "status": "generation_truncated",
            "values": {},
            "reason": "A chunk has no generated EOS; partial transcription is not scored. Increase max_new_tokens.",
        }
    counts = compare_text(
        details["reference_text"], details["hypothesis_text"], normalizer=normalizer
    )
    details.update(counts)
    details["reference_fingerprint"] = {
        unit: counts[unit]["reference_fingerprint"] for unit in ("word", "char")
    }
    if not generation_complete:
        base["warnings"] = [
            "Truncated generated text was scored under explicit truncation_policy=score; no retry, row filtering or denominator substitution."
        ]
        details["scored_truncated_generation"] = True
    return {
        **base,
        "status": "ok" if counts["word"]["N"] else "undefined_reference",
        "values": {"wer": counts["word"]["value"], "cer": counts["char"]["value"]},
    }


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


def generation_limits(model, prompt_rows, max_new_tokens):
    """Validate the requested budget against the actual decoder configuration."""
    if (
        not prompt_rows
        or not prompt_rows[0]
        or any(len(row) != len(prompt_rows[0]) for row in prompt_rows)
    ):
        raise ValueError("Decoder prompts must be nonempty and equally sized")
    start = model.generation_config.decoder_start_token_id
    if start is None:
        start = getattr(model.config, "decoder_start_token_id", None)
    prompt_length = len(prompt_rows[0])
    # GenerationMixin adds decoder_start_token_id when every prompt lacks it.
    if start is not None and all(row[0] != start for row in prompt_rows):
        prompt_length += 1
    decoder = model.get_decoder()
    decoder_config = getattr(decoder, "config", model.config)
    capacity = getattr(decoder_config, "max_position_embeddings", None)
    if capacity is None:
        capacity = getattr(decoder_config, "max_target_positions", None)
    if capacity is None:
        capacity = getattr(model.config, "max_position_embeddings", None)
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
        raise ValueError("Cannot establish the Cohere decoder positional capacity")
    if prompt_length + max_new_tokens > capacity:
        raise ValueError(
            f"Decoder prompt ({prompt_length}) + max_new_tokens ({max_new_tokens}) exceeds actual decoder capacity ({capacity})"
        )
    return prompt_length, capacity


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
    prompt_length, capacity = generation_limits(
        model, inputs["decoder_input_ids"].tolist(), cfg["max_new_tokens"]
    )
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
    health.update(
        chunks=chunk_count,
        audio_chunk_index=[list(x) for x in chunks],
        decoder_prompt_tokens=prompt_length,
        decoder_position_capacity=capacity,
    )
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
    if not audio_reference and not isinstance(reference, str):
        raise ValueError(
            "Cohere WER/CER requires ground-truth reference text (including empty text)"
        )
    if audio_reference and not isinstance(reference, (str, Path)):
        raise ValueError("Cohere dWER/dCER requires a clean-reference audio path")
    wave, hyp_info = read_audio(
        hypothesis, maximum=cfg["max_audio_seconds"], frontend=cfg["audio_frontend"]
    )
    reference_wave, ref_info = (None, None)
    if audio_reference:
        reference_wave, ref_info = read_audio(
            reference, maximum=cfg["max_audio_seconds"], frontend=cfg["audio_frontend"]
        )
    provenance = {"hypothesis": artifact(hypothesis), "model_dir": artifact(path)}
    if config.get("tokenizer_file"):
        tokenizer_path = Path(require(config, "tokenizer_file"))
        if tokenizer_path.resolve() != (Path(path) / "tokenizer.model").resolve():
            raise ValueError("tokenizer_file must identify model_dir/tokenizer.model")
        provenance["tokenizer_file"] = artifact(tokenizer_path)
    elif (Path(path) / "tokenizer.model").is_file():
        provenance["tokenizer_file"] = artifact(Path(path) / "tokenizer.model")
    if audio_reference:
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
    if audio_reference:
        ref_text, ref_decode = _decode(reference_wave, processor, model, cfg)
    else:
        ref_text = reference
    extractor = processor.feature_extractor
    protocol = {
        "family": family,
        "profile": family if family in PROFILE_DEFAULTS else "cohere_transcribe_native_v1",
        "source": SOURCE,
        "model_id": MODEL_ID,
        "scoring_sample_rate": 16000,
        "channel_policy": "float64_arithmetic_mean_channels"
        if cfg["audio_frontend"] == "float64_downmix"
        else "strict_mono",
        "resampler": "soxr_HQ",
        "gain_normalization": "none",
        "silence_policy": "decode_no_vad",
        "normalization": cfg["normalizer"],
        "number_normalization": "upstream_whisper_english"
        if cfg["normalizer"] == "whisper_en"
        else "no_verbalization",
        "word_tokenization": "whitespace_no_implicit_language_segmentation",
        "character_tokenization": "normalized_unicode_letters_marks_numbers_without_spaces"
        if cfg["normalizer"] == "nfkc-casefold-v1"
        else "upstream_normalized_unicode_codepoints_without_whitespace",
        "language": cfg["language"],
        "punctuation": cfg["punctuation"],
        "dtype": cfg["dtype"],
        "beam_size": cfg["beam_size"],
        "do_sample": False,
        "max_new_tokens": cfg["max_new_tokens"],
        "forced_eos_token_id": None,
        "truncation_policy": "reject_missing_generated_eos"
        if cfg["truncation_policy"] == "reject"
        else "score_all_generated_text_with_truncation_warning",
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
        "reference_mode": "clean_reference_asr" if audio_reference else "ground_truth_text",
        "aggregation": "micro_errors_over_reference_units",
        "artifact_hashes": {
            key: provenance[key]["sha256"]
            for key in ("model_dir", "tokenizer_file")
            if key in provenance
        },
    }
    if cfg["audio_frontend"] != "strict_float32":
        protocol["audio_frontend"] = cfg["audio_frontend"]
        protocol["waveform_dtype_order"] = (
            "soundfile_float64; channel_mean; soxr_HQ; contiguous_float32"
        )
    if cfg["normalizer"] != "nfkc-casefold-v1":
        protocol["normalization_source"] = "espnet2.text.cleaner.TextCleaner"
        protocol["edit_counts"] = "python_Levenshtein.opcodes_reference_span_except_insert"
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
    if cfg["normalizer"] != "nfkc-casefold-v1":
        backend.update({pkg: version(pkg) for pkg in ("espnet", "openai-whisper", "Levenshtein")})
    details = {
        "hypothesis_text": hyp_text,
        "reference_text": ref_text,
        "hypothesis_audio": hyp_info,
        "reference_audio": ref_info,
        "hypothesis_decode": hyp_decode,
        "reference_decode": ref_decode,
        "normalization_backend": {
            "normalizer": cfg["normalizer"],
            "versions": {
                pkg: backend[pkg]
                for pkg in (
                    ("meeteval", "kaldialign")
                    if cfg["normalizer"] == "nfkc-casefold-v1"
                    else ("espnet", "openai-whisper", "Levenshtein")
                )
            },
        },
    }
    base = {"protocol": protocol, "backend": backend, "provenance": provenance, "details": details}
    return finalize_score(
        base, normalizer=cfg["normalizer"], truncation_policy=cfg["truncation_policy"]
    )
