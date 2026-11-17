"""Validate additive Cohere scoring profiles with real, local model execution.

Run in the isolated Cohere environment with the candidate package importable:
  python scripts/validate_cohere_profiles.py --model-dir /models/cohere \
      --manifest pairs.json --output validation.json --device cuda:0

Manifest records have key, paths.ref, paths.inf, and optionally reference_text.
Use --chinese-audio for Chinese interface/identity tests. Without --chinese-text,
the native model's transcript is used ONLY as a self-transcript interface check,
never as a claimed ground-truth accuracy measurement.

--reference-script optionally executes a locally authorized original evaluation
script, in place, to compare its actual load_model/read_audio/transcribe_batch/
levenshtein_metric functions. This is trusted Python execution: supply only a
script you are authorized to execute. No reference source, model, or audio is
copied or downloaded. Bytecode writing is disabled before that import. Without
it, the public native Transformers example is the independent inference path.
The compatibility comparison deliberately uses one utterance per native call;
it does not establish equality with historical duration-sorted batches of eight.
For a small CPU comparison, use --reference-script /authorized/original.py
--reference-only --limit 1; this skips the legacy, truncation and Chinese cases.
"""

import argparse
import gc
import hashlib
import importlib.util
from importlib.metadata import version
import inspect
import json
from pathlib import Path
import sys
import time

import Levenshtein
import numpy as np
import soundfile as sf
import soxr
import torch
from espnet2.text.cleaner import TextCleaner
from transformers import AutoProcessor, CohereAsrForConditionalGeneration
from whisper.normalizers import BasicTextNormalizer, EnglishTextNormalizer

from speechmetrichub import evaluate, run
from speech_eval.transcription import tokenize


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def original_script(path):
    if path is None:
        return None
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("authorized_cohere_reference", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("load_model", "read_audio", "transcribe_batch", "levenshtein_metric"):
        if not callable(getattr(module, name, None)):
            raise ValueError(f"Reference script is missing {name}")
    return module


def audio(path):
    wave, rate = sf.read(path, always_2d=False)
    if wave.ndim > 1:
        wave = wave.mean(axis=-1)
    if rate != 16000:
        wave = soxr.resample(wave, rate, 16000)
    return np.ascontiguousarray(wave, dtype=np.float32)


def independent_counts(reference, hypothesis, normalizer, unit):
    if normalizer == "nfkc-casefold-v1":
        left, right = tokenize(reference, unit), tokenize(hypothesis, unit)
    else:
        cleaner = EnglishTextNormalizer() if normalizer == "whisper_en" else BasicTextNormalizer()
        left, right = cleaner(reference), cleaner(hypothesis)
        left, right = [
            text.split() if unit == "word" else [c for c in text if not c.isspace()]
            for text in (left, right)
        ]
    counts = {"N": len(left), "S": 0, "D": 0, "I": 0}
    names = {"replace": "S", "delete": "D", "insert": "I"}
    for op, a, b, c, d in Levenshtein.opcodes(left, right):
        if op in names:
            counts[names[op]] += d - c if op == "insert" else b - a
    counts["errors"] = counts["S"] + counts["D"] + counts["I"]
    counts["value"] = 100 * counts["errors"] / counts["N"] if counts["N"] else None
    return counts


def native_decode(module, model, processor, path, language="en", punctuation=False, budget=256):
    wave = module.read_audio(str(path)) if module else audio(path)
    with torch.inference_mode():
        if module:
            texts = module.transcribe_batch(model, processor, [wave], language, punctuation, budget)
        else:
            inputs = processor(
                [wave],
                sampling_rate=16000,
                return_tensors="pt",
                language=language,
                punctuation=punctuation,
            )
            chunks = inputs.get("audio_chunk_index")
            inputs = inputs.to(model.device, dtype=model.dtype)
            tokens = model.generate(**inputs, max_new_tokens=budget)
            texts = processor.decode(
                tokens, skip_special_tokens=True, audio_chunk_index=chunks, language=language
            )
    if isinstance(texts, str):
        texts = [texts]
    if len(texts) != 1:
        raise ValueError(f"Native batch-one decode returned {len(texts)} transcripts")
    return texts[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--reference-script", type=Path)
    parser.add_argument("--reference-only", action="store_true")
    parser.add_argument("--chinese-audio", type=Path)
    parser.add_argument("--chinese-text")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--limit", type=int, default=2)
    args = parser.parse_args()
    if args.limit < 1 or (args.chinese_text is not None and args.chinese_audio is None):
        parser.error("Positive --limit required; --chinese-text needs --chinese-audio")
    if args.reference_only and args.reference_script is None:
        parser.error("--reference-only requires --reference-script")
    rows = [
        r
        for r in json.loads(args.manifest.read_text())["records"]
        if not r.get("is_clipped", False)
    ][: args.limit]
    if not rows:
        parser.error("Manifest must contain at least one uncut real audio pair")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "purpose": "real inference, normalization, S/D/I parity and bounded-generation accounting",
        "utterance_batch_size": 1,
        "historical_batch8_parity_claimed": False,
        "reference_only": args.reference_only,
        "versions": {
            p: version(p)
            for p in (
                "torch",
                "transformers",
                "openai-whisper",
                "espnet",
                "Levenshtein",
                "numpy",
                "soundfile",
                "soxr",
            )
        },
        "normalizer_source_sha256": {
            cls.__name__: digest(inspect.getfile(cls))
            for cls in (BasicTextNormalizer, EnglishTextNormalizer, TextCleaner)
        },
        "reference_script_sha256": digest(args.reference_script) if args.reference_script else None,
        "checks": [],
        "cases": [],
    }
    report["normalizer_source_sha256"]["english.json"] = digest(
        Path(inspect.getfile(EnglishTextNormalizer)).with_name("english.json")
    )

    def check(name, condition, **details):
        report["checks"].append({"name": name, "passed": bool(condition), **details})

    def save():
        report["passed"] = all(item["passed"] for item in report["checks"])
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    torch.set_num_threads(2)
    upstream = original_script(args.reference_script)
    if upstream:
        model, processor = upstream.load_model(str(args.model_dir), args.device)
    else:
        processor = AutoProcessor.from_pretrained(
            args.model_dir, local_files_only=True, trust_remote_code=False
        )
        model = (
            CohereAsrForConditionalGeneration.from_pretrained(
                args.model_dir,
                local_files_only=True,
                trust_remote_code=False,
                use_safetensors=True,
                dtype=torch.float32 if args.device == "cpu" else torch.bfloat16,
            )
            .to(args.device)
            .eval()
        )
    report["native_generation_config"] = model.generation_config.to_dict()
    check(
        "native_checkpoint_does_not_force_eos", model.generation_config.forced_eos_token_id is None
    )
    native = []
    for row in rows:
        ref, hyp = row["paths"]["ref"], row["paths"]["inf"]
        if upstream:
            check(
                f"{row['key']}:waveform_frontend_parity",
                np.array_equal(upstream.read_audio(ref), audio(ref))
                and np.array_equal(upstream.read_audio(hyp), audio(hyp)),
            )
        result = {
            "key": row["key"],
            "reference": native_decode(upstream, model, processor, ref),
            "hypothesis": native_decode(upstream, model, processor, hyp),
        }
        if upstream:
            result["original_word_counts"] = upstream.levenshtein_metric(
                TextCleaner("whisper_en"), result["reference"], result["hypothesis"]
            )
            result["original_gt_word_counts"] = upstream.levenshtein_metric(
                TextCleaner("whisper_en"),
                row.get("reference_text") or result["reference"],
                result["hypothesis"],
            )
        native.append(result)
        print(f"Native English pair complete: {row['key']}", flush=True)
    cap_native = (
        None
        if args.reference_only
        else native_decode(upstream, model, processor, rows[0]["paths"]["inf"], budget=1)
    )
    zh_native = (
        native_decode(upstream, model, processor, args.chinese_audio, language="zh")
        if args.chinese_audio and not args.reference_only
        else None
    )
    del model, processor
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    base = {
        "model_dir": str(args.model_dir.resolve()),
        "python": sys.executable,
        "device": args.device,
        "threads": 2,
        "timeout": 1200,
    }

    def execute(name, metric, reference, hypothesis, config=None):
        started = time.perf_counter()
        result = run(
            metric, reference=reference, hypothesis=hypothesis, config={**base, **(config or {})}
        )
        report["cases"].append(
            {
                "name": name,
                "metric": metric,
                "result": result,
                "wall_seconds": time.perf_counter() - started,
            }
        )
        print(f"Library case complete: {name}: {result.get('status')}", flush=True)
        save()
        return result

    def verify(name, result, reference, hypothesis, normalizer, unit, exact_counts=True):
        expected = independent_counts(reference, hypothesis, normalizer, unit)
        check(
            name + ":status",
            result.get("status") == ("ok" if expected["N"] else "undefined_reference"),
        )
        keys = ("N", "S", "D", "I", "errors", "value") if exact_counts else ("N", "errors", "value")
        check(name + ":counts", all(result.get(k) == expected[k] for k in keys), expected=expected)
        check(
            name + ":native_transcripts",
            result.get("details", {}).get("hypothesis_text") == hypothesis
            and result.get("details", {}).get("reference_text") == reference,
        )

    for row, direct in zip(rows, native):
        gt = row.get("reference_text") or direct["reference"]
        gt_kind = (
            "provided_transcript"
            if row.get("reference_text")
            else "self_transcript_interface_check_not_accuracy"
        )
        gt_result = execute(row["key"] + ":en_gt", "cohere_wer_en_whisper", gt, row["paths"]["inf"])
        gt_result["validation_reference_kind"] = gt_kind
        verify(row["key"] + ":en_gt", gt_result, gt, direct["hypothesis"], "whisper_en", "word")
        audio_result = execute(
            row["key"] + ":en_audio",
            "cohere_dwer_en_whisper",
            row["paths"]["ref"],
            row["paths"]["inf"],
        )
        verify(
            row["key"] + ":en_audio",
            audio_result,
            direct["reference"],
            direct["hypothesis"],
            "whisper_en",
            "word",
        )
        if upstream:
            original = direct["original_word_counts"]
            check(
                row["key"] + ":original_sdi",
                all(
                    audio_result.get(key) == original[old]
                    for key, old in (("S", "replace"), ("D", "delete"), ("I", "insert"))
                )
                and audio_result.get("N")
                == sum(original[k] for k in ("equal", "replace", "delete")),
            )
            original_gt = direct["original_gt_word_counts"]
            check(
                row["key"] + ":original_gt_sdi",
                all(
                    gt_result.get(key) == original_gt[old]
                    for key, old in (("S", "replace"), ("D", "delete"), ("I", "insert"))
                )
                and gt_result.get("N")
                == sum(original_gt[k] for k in ("equal", "replace", "delete")),
            )

    if args.reference_only:
        report["other_runtime_cases"] = "not_requested_reference_only"
        save()
        print(
            json.dumps(
                {
                    "passed": report["passed"],
                    "checks": len(report["checks"]),
                    "output": str(args.output),
                }
            ),
            flush=True,
        )
        return 0 if report["passed"] else 1

    first = rows[0]
    gt = first.get("reference_text") or native[0]["reference"]
    for metrics, reference in (
        (["cohere_wer", "cohere_cer"], gt),
        (["cohere_dwer", "cohere_dcer"], first["paths"]["ref"]),
    ):
        family = "cohere_dwer" if metrics[0] == "cohere_dwer" else "cohere_wer"
        results = evaluate(
            metrics, reference=reference, hypothesis=first["paths"]["inf"], configs={family: base}
        )
        for metric, result in results.items():
            report["cases"].append(
                {"name": "legacy_interface:" + metric, "metric": metric, "result": result}
            )
            # These are legacy-interface smoke/count checks, not a new native
            # parity claim: their punctuation and float32 frontend are unchanged.
            details = result.get("details", {})
            verify(
                metric,
                result,
                details.get("reference_text", ""),
                details.get("hypothesis_text", ""),
                "nfkc-casefold-v1",
                "char" if metric.endswith("cer") else "word",
                exact_counts=False,
            )

    scored = execute(
        "budget1_score", "cohere_wer_en_whisper", gt, first["paths"]["inf"], {"max_new_tokens": 1}
    )
    verify("budget1_score", scored, gt, cap_native, "whisper_en", "word")
    rejected = execute(
        "budget1_reject",
        "cohere_wer_en_whisper",
        gt,
        first["paths"]["inf"],
        {"max_new_tokens": 1, "truncation_policy": "reject"},
    )
    check(
        "budget1_has_real_missing_eos",
        scored.get("details", {}).get("hypothesis_decode", {}).get("complete") is False,
    )
    check("budget1_scored_with_visible_warning", bool(scored.get("warnings")))
    check(
        "budget1_reject_preserves_same_transcript_without_score",
        rejected.get("status") == "generation_truncated"
        and rejected.get("value") is None
        and rejected.get("details", {}).get("hypothesis_text") == cap_native,
    )

    if args.chinese_audio:
        zh_gt = args.chinese_text if args.chinese_text is not None else zh_native
        zh_result = execute("zh_gt", "cohere_cer_zh_basic", zh_gt, args.chinese_audio)
        zh_result["validation_reference_kind"] = (
            "provided_transcript"
            if args.chinese_text is not None
            else "self_transcript_interface_check_not_accuracy"
        )
        verify("zh_gt", zh_result, zh_gt, zh_native, "whisper_basic", "char")
        zh_audio = execute(
            "zh_audio_identity", "cohere_dcer_zh_basic", args.chinese_audio, args.chinese_audio
        )
        verify("zh_audio_identity", zh_audio, zh_native, zh_native, "whisper_basic", "char")
    else:
        report["chinese_runtime"] = "not_requested_not_validated"
    report["normalizer_controls"] = {
        "english": {
            s: EnglishTextNormalizer()(s)
            for s in ("Uh, I paid twenty one dollars.", "He cannot colour it.")
        },
        "chinese_basic": {
            s: BasicTextNormalizer()(s)
            for s in ("我有１２个。", "我有十二个。", "繁體與简体", "你好[噪声]。")
        },
    }
    check(
        "basic_chinese_does_not_equate_written_numerals",
        BasicTextNormalizer()("我有12个") != BasicTextNormalizer()("我有十二个"),
    )
    save()
    print(
        json.dumps(
            {
                "passed": report["passed"],
                "checks": len(report["checks"]),
                "output": str(args.output),
            }
        ),
        flush=True,
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
