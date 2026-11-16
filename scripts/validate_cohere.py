"""Validate local Cohere metrics against native Transformers generation.

Run this script in the separately provisioned Cohere environment, with the
candidate SpeechMetricHub importable. No weights, audio or code are downloaded.

  python scripts/validate_cohere.py --model-dir /path/to/cohere-model \
      --manifest /path/to/manifest.json --device cuda:0 --dtype bfloat16 \
      --output /path/to/cohere-validation.json

Manifest: {"records": [{"key": "example", "paths": {"ref": "clean.wav",
"inf": "generated.wav"}, "reference_text": "Correct complete transcript",
"is_clipped": false}]}. Audio-reference comparisons use paths.ref; GT cases
require an explicit nonempty reference_text and must not be marked clipped.
The default limit is three real pairs plus generated controls. CUDA device IDs
are logical IDs within the caller's CUDA_VISIBLE_DEVICES setting.
"""

import argparse
import gc
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
import math
from pathlib import Path
import platform
import sys
import time

import numpy as np
import soundfile as sf
import soxr
import torch
from transformers import AutoProcessor, CohereAsrForConditionalGeneration

from speechmetrichub import evaluate, run
from speech_eval.transcription import tokenize


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def edit_distance(reference, hypothesis):
    """Independent Levenshtein total; S/D/I tie-breaking need not be unique."""
    previous = list(range(len(hypothesis) + 1))
    for i, left in enumerate(reference, 1):
        current = [i]
        for j, right in enumerate(hypothesis, 1):
            current.append(min(previous[j] + 1, current[-1] + 1, previous[j - 1] + (left != right)))
        previous = current
    return previous[-1]


def expected_counts(reference, hypothesis, unit):
    a, b = tokenize(reference, unit), tokenize(hypothesis, unit)
    errors = edit_distance(a, b)
    return {"N": len(a), "errors": errors, "value": 100 * errors / len(a) if a else None}


def read_audio(path):
    wave, sr = sf.read(path, dtype="float32")
    if wave.ndim != 1 or not wave.size or not np.isfinite(wave).all():
        raise ValueError("Validation inputs must be nonempty finite mono audio")
    return soxr.resample(wave, sr, 16000, quality="HQ") if sr != 16000 else wave


def native_decode(processor, model, path, settings):
    audio = read_audio(path)
    start = time.perf_counter()
    inputs = processor(
        audio,
        sampling_rate=16000,
        return_tensors="pt",
        language=settings["language"],
        punctuation=settings["punctuation"],
    )
    chunk_index = inputs.get("audio_chunk_index")
    prompt_length = inputs["decoder_input_ids"].shape[-1]
    chunks = int(inputs["input_features"].shape[0])
    sequences = []
    with torch.inference_mode():
        for begin in range(0, chunks, settings["chunk_batch_size"]):
            batch = {
                key: value[begin : begin + settings["chunk_batch_size"]].to(
                    model.device, dtype=model.dtype if value.is_floating_point() else value.dtype
                )
                for key, value in inputs.items()
                if isinstance(value, torch.Tensor)
            }
            output = model.generate(
                **batch,
                num_beams=settings["beam_size"],
                do_sample=False,
                max_new_tokens=settings["max_new_tokens"],
                forced_eos_token_id=None,
                return_dict_in_generate=False,
            )
            sequences.extend(output.detach().cpu().tolist())
    if model.device.type == "cuda":
        torch.cuda.synchronize(model.device)
    padding = model.generation_config.pad_token_id
    if padding is None:
        padding = processor.tokenizer.pad_token_id
    length = max(map(len, sequences))
    tokens = torch.tensor([row + [padding] * (length - len(row)) for row in sequences])
    upstream_empty_reassembly_error = False
    try:
        decoded = processor.decode(
            tokens,
            skip_special_tokens=True,
            audio_chunk_index=chunk_index,
            language=settings["language"],
        )
    except IndexError:
        raw = processor.tokenizer.decode(tokens, skip_special_tokens=True)
        raw = [raw] if isinstance(raw, str) else raw
        if not raw or any(text.strip() for text in raw):
            raise
        # Native 5.4 reassembly can index an empty list after all chunks decode
        # empty. Validate the adapter's explicit empty-output guard separately.
        decoded = [""]
        upstream_empty_reassembly_error = True
    if not isinstance(decoded, list) or len(decoded) != 1:
        raise ValueError(f"Expected one reassembled transcript, got {decoded!r}")
    eos = model.generation_config.eos_token_id
    if eos is None:
        eos = model.config.eos_token_id
    eos = [eos] if isinstance(eos, int) else list(eos)
    suffixes = tokens[:, prompt_length:].detach().cpu().tolist()
    stopped = [any(token in eos for token in row) for row in suffixes]
    return dict(
        text=decoded[0],
        complete=all(stopped),
        eos_per_chunk=stopped,
        generated_tokens=suffixes,
        decoder_prompt_tokens=int(prompt_length),
        audio_chunk_index=chunk_index,
        chunks=len(suffixes),
        seconds=len(audio) / 16000,
        upstream_empty_reassembly_error=upstream_empty_reassembly_error,
        elapsed_seconds=time.perf_counter() - start,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--dtype", choices=("float32", "bfloat16"), default="bfloat16")
    parser.add_argument("--language", default="en")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--worker-python", default=sys.executable)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--chunk-batch-size", type=int, default=1)
    args = parser.parse_args()
    if args.limit < 1:
        parser.error("--limit must be positive")
    torch.set_num_threads(2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    controls = args.output.parent / "cohere-controls"
    controls.mkdir(exist_ok=True)
    manifest = json.loads(args.manifest.read_text())
    rows = [
        row
        for row in manifest["records"]
        if row.get("reference_text") and not row.get("is_clipped", False)
    ][: args.limit]
    if not rows:
        parser.error("Manifest needs at least one untruncated pair with ground-truth text")
    config = dict(
        model_dir=str(args.model_dir.resolve()),
        python=args.worker_python,
        device=args.device,
        dtype=args.dtype,
        language=args.language,
        punctuation=True,
        beam_size=1,
        max_new_tokens=args.max_new_tokens,
        chunk_batch_size=args.chunk_batch_size,
        max_audio_seconds=600,
        threads=2,
        timeout=1200,
    )
    cases = [
        dict(
            key=row["key"],
            reference=str(row["paths"]["ref"]),
            hypothesis=str(row["paths"]["inf"]),
            reference_text=row["reference_text"],
            kind="real_pair",
        )
        for row in rows
    ]
    base = read_audio(rows[0]["paths"]["ref"])
    silence = np.zeros(3 * 16000, dtype=np.float32)
    noise = np.random.default_rng(20261116).normal(0, 0.01, 3 * 16000).astype(np.float32)
    for name, wave in [("silence", silence), ("noise", noise)]:
        path = controls / f"{name}.wav"
        sf.write(path, wave, 16000, subtype="FLOAT")
        cases.append(
            dict(
                key=name,
                reference=str(path),
                hypothesis=str(path),
                reference_text="",
                kind="non_speech",
            )
        )
    repetitions = math.ceil(40 * 16000 / len(base))
    long_audio = np.concatenate([base] * repetitions)
    long_path = controls / "long_repeated_speech.wav"
    sf.write(long_path, long_audio, 16000, subtype="FLOAT")
    cases.append(
        dict(
            key="long_repeated_speech",
            reference=str(long_path),
            hypothesis=str(long_path),
            reference_text=" ".join([rows[0]["reference_text"]] * repetitions),
            kind="long_form",
        )
    )
    packages = {}
    for name in (
        "torch",
        "transformers",
        "huggingface-hub",
        "tokenizers",
        "numpy",
        "librosa",
        "soundfile",
        "soxr",
        "meeteval",
        "kaldialign",
    ):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    report = dict(
        schema_version=1,
        platform=platform.platform(),
        python=sys.version,
        packages=packages,
        config=config,
        manifest_sha256=file_hash(args.manifest),
        sources=[
            "https://huggingface.co/CohereLabs/cohere-transcribe-03-2026",
            "https://github.com/huggingface/transformers/tree/v5.4.0/src/transformers/models/cohere_asr",
        ],
        protocol="Matched local weights, float32/soxr HQ audio, native processor and generate/decode. Shared declared normalizer; independent Levenshtein N/errors oracle.",
        cases=cases,
        native={},
        checks=[],
        invalid_inputs=[],
    )

    def save():
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False))

    for case in cases:
        case["input_sha256"] = {k: file_hash(case[k]) for k in ("reference", "hypothesis")}
    start = time.perf_counter()
    processor = AutoProcessor.from_pretrained(
        args.model_dir, local_files_only=True, trust_remote_code=False
    )
    model = (
        CohereAsrForConditionalGeneration.from_pretrained(
            args.model_dir,
            local_files_only=True,
            trust_remote_code=False,
            use_safetensors=True,
            dtype=getattr(torch, args.dtype),
        )
        .to(args.device)
        .eval()
    )
    if model.device.type == "cuda":
        torch.cuda.synchronize(model.device)
    report["native_model_load_seconds"] = time.perf_counter() - start
    report["processor_settings"] = {
        name: getattr(processor.feature_extractor, name, None)
        for name in (
            "sampling_rate",
            "hop_length",
            "n_fft",
            "win_length",
            "preemphasis",
            "dither",
            "max_audio_clip_s",
            "overlap_chunk_second",
            "min_energy_window_samples",
        )
    }
    for path in dict.fromkeys(case[key] for case in cases for key in ("reference", "hypothesis")):
        result = native_decode(processor, model, path, config)
        report["native"][path] = result
        save()
        print("native", Path(path).name, result["chunks"], result["complete"], flush=True)
    trunc_config = {**config, "max_new_tokens": 1}
    report["native_truncated"] = native_decode(
        processor, model, cases[0]["hypothesis"], trunc_config
    )
    del model, processor
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    save()

    for case in cases:
        hyp_native = report["native"][case["hypothesis"]]
        ref_native = report["native"][case["reference"]]
        for family, ids, reference, text in (
            (
                "cohere_wer",
                ["cohere_wer", "cohere_cer"],
                case["reference_text"],
                case["reference_text"],
            ),
            ("cohere_dwer", ["cohere_dwer", "cohere_dcer"], case["reference"], ref_native["text"]),
        ):
            start = time.perf_counter()
            results = evaluate(
                ids, reference=reference, hypothesis=case["hypothesis"], configs={family: config}
            )
            elapsed = time.perf_counter() - start
            for metric in ids:
                actual = results[metric]
                expected = expected_counts(
                    text, hyp_native["text"], "char" if metric.endswith("cer") else "word"
                )
                details = actual.get("details", {})
                text_equal = (
                    details.get("hypothesis_text") == hyp_native["text"]
                    and details.get("reference_text") == text
                )
                finished = hyp_native["complete"] and (
                    family == "cohere_wer" or ref_native["complete"]
                )
                if not finished:
                    passed = (
                        actual["status"] == "generation_truncated" and actual.get("value") is None
                    )
                else:
                    passed = (
                        text_equal
                        and actual.get("N") == expected["N"]
                        and actual.get("errors") == expected["errors"]
                    )
                    passed = passed and (
                        (actual.get("value") is None and actual["status"] == "undefined_reference")
                        if expected["value"] is None
                        else (
                            actual["status"] == "ok"
                            and abs(actual["value"] - expected["value"]) < 1e-10
                        )
                    )
                if case["kind"] == "long_form":
                    passed = passed and hyp_native["chunks"] > 1
                report["checks"].append(
                    dict(
                        key=case["key"],
                        metric=metric,
                        expected=expected,
                        exact_native_text_match=text_equal,
                        actual=actual,
                        passed=passed,
                        family_call_wall_seconds=elapsed,
                    )
                )
                save()
                print("adapter", case["key"], metric, "PASS" if passed else "FAIL", flush=True)
    result = run(
        "cohere_wer",
        reference=cases[0]["reference_text"],
        hypothesis=cases[0]["hypothesis"],
        config=trunc_config,
    )
    report["token_budget_check"] = dict(
        result=result,
        passed=(
            not report["native_truncated"]["complete"]
            and result["status"] == "generation_truncated"
            and result.get("value") is None
        ),
    )

    # These must fail before model scoring, with no fabricated zero error.
    stereo = controls / "invalid_stereo.wav"
    sf.write(stereo, np.zeros((16000, 2)), 16000)
    too_short = controls / "invalid_short.wav"
    sf.write(too_short, np.zeros(80), 16000)
    for name, path, override in [
        ("stereo", stereo, {}),
        ("short", too_short, {}),
        ("duration_limit", long_path, {"max_audio_seconds": 1}),
        ("unsupported_language", Path(cases[0]["hypothesis"]), {"language": "xx"}),
    ]:
        result = run(
            "cohere_wer", reference="test", hypothesis=str(path), config={**config, **override}
        )
        report["invalid_inputs"].append(
            dict(
                case=name,
                result=result,
                passed=result.get("value") is None and result["status"] == "invalid_input",
            )
        )
        save()
    scored_ids = sorted(
        {
            check["metric"]
            for check in report["checks"]
            if check["actual"]["status"] == "ok" and check["passed"]
        }
    )
    report["summary"] = dict(
        real_pairs=len(rows),
        metric_checks=len(report["checks"]),
        metric_checks_passed=sum(check["passed"] for check in report["checks"]),
        invalid_checks_passed=sum(check["passed"] for check in report["invalid_inputs"]),
        token_budget_check_passed=report["token_budget_check"]["passed"],
        successfully_scored_metric_ids=scored_ids,
    )
    report["complete"] = (
        all(check["passed"] for check in report["checks"] + report["invalid_inputs"])
        and report["token_budget_check"]["passed"]
        and len(scored_ids) == 4
    )
    save()
    print(json.dumps(report["summary"], indent=2), flush=True)
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
