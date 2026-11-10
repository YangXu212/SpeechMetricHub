"""Independent CPU validation against pinned upstream source and waveform controls.

Run from a source checkout with the candidate SpeechMetricHub installed:

  python scripts/validate_pitch.py --manifest /path/to/manifest.json \
      --upstream-dir /tmp/pitch-upstream --download-upstream \
      --output /tmp/pitch-validation.json

The manifest must have a ``records`` list; each record contains ``key`` and
``paths`` with ``ref`` and ``inf`` paired mono WAV paths. Use at least one pair.
Install the pitch extra plus torch, which the original Amphion scorer imports.
Downloads occur only with --download-upstream, use pinned public revisions,
and are verified against validation/pitch-sources.json before execution.
Upstream function bodies are compiled unchanged from their downloaded AST;
only unrelated package imports are omitted. No scorer is mocked or replaced.
"""

import argparse
import ast
import hashlib
import importlib.metadata as metadata
import importlib.util
import json
import math
from pathlib import Path
import platform
import sys
import time
import types
from urllib.request import urlopen

import librosa
import numpy as np
import parselmouth
import pyworld
import soundfile as sf
import torch

from speechmetrichub import run, evaluate_batch

ROOT = Path(__file__).resolve().parents[1]


def canonical_source(data):
    return (data.decode("utf-8").replace("\r\n", "\n").rstrip("\r\n") + "\n").encode("utf-8")


def prepare_upstream(directory, download):
    manifest = json.loads((ROOT / "validation/pitch-sources.json").read_text(encoding="utf-8-sig"))
    for source in manifest["sources"]:
        target = directory / source["relative_path"]
        if not target.exists():
            if not download:
                raise FileNotFoundError(
                    f"{target}; pass --download-upstream to fetch pinned public sources"
                )
            with urlopen(source["raw_url"], timeout=60) as response:
                content = response.read()
            if hashlib.sha256(canonical_source(content)).hexdigest() != source["sha256_lf"]:
                raise ValueError(f"Upstream checksum mismatch: {source['raw_url']}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(canonical_source(content))
        actual = hashlib.sha256(canonical_source(target.read_bytes())).hexdigest()
        if actual != source["sha256_lf"]:
            raise ValueError(f"Upstream source modified or wrong version: {target}")
    return manifest["sources"]


def exact_definitions(file, names, namespace):
    """Execute original AST definitions, not retyped implementations."""
    tree = ast.parse(file.read_text(encoding="utf-8"))
    chosen = [
        n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in names
    ]
    assert {n.name for n in chosen} == set(names)
    exec(compile(ast.Module(body=chosen, type_ignores=[]), str(file), "exec"), namespace)


def upstream_modules(upstream_dir):
    UP = upstream_dir
    util = types.ModuleType("utils.util")
    exact_definitions(UP / "Amphion/utils/util.py", ["JsonHParams"], util.__dict__)
    f0 = types.ModuleType("utils.f0")
    f0.__dict__.update(np=np, torch=torch, parselmouth=parselmouth)
    exact_definitions(
        UP / "Amphion/utils/f0.py",
        ["get_f0_features_using_parselmouth", "get_pitch_sub_median"],
        f0.__dict__,
    )
    modules = {}
    for filename in ("f0_rmse", "v_uv_f1"):
        namespace = dict(
            np=np,
            torch=torch,
            math=math,
            librosa=librosa,
            JsonHParams=util.JsonHParams,
            get_f0_features_using_parselmouth=f0.get_f0_features_using_parselmouth,
            get_pitch_sub_median=f0.get_pitch_sub_median,
        )
        name = "extract_f0rmse" if filename == "f0_rmse" else "extract_f1_v_uv"
        exact_definitions(UP / f"Amphion/evaluation/metrics/f0/{filename}.py", [name], namespace)
        modules[filename] = namespace[name]
    path = UP / "ESPnet/egs2/TEMPLATE/asr1/pyscripts/utils/evaluate_f0.py"
    spec = importlib.util.spec_from_file_location("espnet_f0_oracle", path)
    espnet = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(espnet)
    return modules, espnet


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def world_oracle(ref_path, hyp_path):
    ref, sr = sf.read(ref_path, dtype="float64")
    hyp, sr2 = sf.read(hyp_path, dtype="float64")
    assert sr == sr2 and len(ref) == len(hyp)
    a = pyworld.harvest(ref, sr, f0_floor=50, f0_ceil=800, frame_period=5.0)[0]
    b = pyworld.harvest(hyp, sr, f0_floor=50, f0_ceil=800, frame_period=5.0)[0]
    assert len(a) == len(b)
    av, bv = a > 0, b > 0
    tp, fp, fn = int(np.sum(av & bv)), int(np.sum(~av & bv)), int(np.sum(av & ~bv))
    den = 2 * tp + fp + fn
    f1 = 2 * tp / den if den else None
    common = av & bv
    rmse = float(np.sqrt(np.mean((a[common] - b[common]) ** 2))) if common.any() else None
    return {"vuv_f1": f1, "f0_rmse": rmse}, {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "common_voiced": int(common.sum()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("outputs/pitch-validation.json"))
    parser.add_argument("--upstream-dir", type=Path, default=Path(".cache/pitch-upstream"))
    parser.add_argument("--download-upstream", action="store_true")
    parser.add_argument("--limit", type=int, default=12)
    args = parser.parse_args()
    torch.set_num_threads(2)
    sources = prepare_upstream(args.upstream_dir, args.download_upstream)
    amphion, espnet = upstream_modules(args.upstream_dir)
    manifest = json.loads(args.manifest.read_text())
    rows = manifest["records"][: args.limit]
    if not rows or args.limit < 1:
        parser.error("Provide at least one record and --limit >= 1")
    versions = {
        p: metadata.version(p)
        for p in [
            "numpy",
            "scipy",
            "librosa",
            "praat-parselmouth",
            "pyworld",
            "pysptk",
            "fastdtw",
            "soundfile",
            "torch",
        ]
    }
    report = dict(
        platform=platform.platform(),
        python=sys.version,
        packages=versions,
        device="CPU",
        manifest_sha256=digest(args.manifest),
        inputs=[],
        parity=[],
        controls=[],
        upstream_sources=sources,
        upstream_execution="Unmodified upstream AST function/class bodies; unrelated imports omitted. ESPnet complete module imported. No numerical mocks.",
        tolerances={"f1": 1e-12, "rmse": 1e-8},
    )
    for src in report["upstream_sources"]:
        src["sha256_raw_local_file"] = digest(args.upstream_dir / src["relative_path"])

    def save():
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False))

    def compare(metric, key, expected, inputs, label, counts=None):
        start = time.perf_counter()
        actual = run(metric, **inputs)
        elapsed = time.perf_counter() - start
        tol = 1e-12 if "f1" in metric else 1e-8
        delta = (
            abs(actual["value"] - expected)
            if actual.get("value") is not None and expected is not None
            else None
        )
        passed = (
            (actual["status"] == "ok" and delta is not None and delta <= tol)
            if expected is not None
            else (actual.get("value") is None and actual["status"].startswith("undefined"))
        )
        record = dict(
            metric=metric,
            key=key,
            oracle=label,
            expected=expected,
            actual=actual,
            absolute_difference=delta,
            passed=passed,
            adapter_seconds=elapsed,
        )
        if counts is not None:
            record["oracle_counts"] = counts
        report["parity"].append(record)
        save()
        print(metric, key, "PASS" if passed else "FAIL", delta, flush=True)

    for i, row in enumerate(rows):
        paths = row["paths"]
        ref, hyp = paths["ref"], paths["inf"]
        report["inputs"].append(
            dict(key=row["key"], reference_sha256=digest(ref), hypothesis_sha256=digest(hyp))
        )
        expected, counts = world_oracle(ref, hyp)
        for metric in ("vuv_f1", "f0_rmse"):
            compare(
                metric,
                row["key"],
                expected[metric],
                dict(reference=ref, hypothesis=hyp),
                "direct WORLD Harvest + independent NumPy counts/errors",
                counts,
            )
        for method in ("cut", "dtw") if i < 2 else ("cut",):
            kw = dict(fs=24000, method=method, need_mean=False)
            tp, fp, fn = amphion["v_uv_f1"](ref, hyp, kwargs=kw)
            denominator = 2 * tp + fp + fn
            expected_f1 = 2 * tp / denominator if denominator else None
            compare(
                "vuv_f1_amphion",
                row["key"],
                expected_f1,
                dict(reference=ref, hypothesis=hyp, sample_rate=24000, method=method),
                "Amphion original extract_f1_v_uv, " + method,
                dict(TP=tp, FP=fp, FN=fn),
            )
            expected_rmse = amphion["f0_rmse"](ref, hyp, kwargs=kw)
            compare(
                "f0_rmse_amphion",
                row["key"],
                expected_rmse,
                dict(reference=ref, hypothesis=hyp, sample_rate=24000, method=method),
                "Amphion original extract_f0rmse, " + method,
            )
        settings = argparse.Namespace(
            f0min=40, f0max=800, n_fft=1024, n_shift=256, mcep_dim=None, mcep_alpha=None
        )
        result = {}
        espnet.calculate([hyp], [ref], settings, result)
        expected_log = next(iter(result.values()))
        expected_log = float(expected_log) if np.isfinite(expected_log) else None
        compare(
            "log_f0_rmse_espnet",
            row["key"],
            expected_log,
            dict(reference=ref, hypothesis=hyp),
            "ESPnet original calculate",
        )

    # Verify default Amphion resampling at 22050 Hz against upstream fs=None.
    ref, hyp = rows[0]["paths"]["ref"], rows[0]["paths"]["inf"]
    kw = dict(fs=None, method="cut", need_mean=False)
    tp, fp, fn = amphion["v_uv_f1"](ref, hyp, kwargs=kw)
    den = 2 * tp + fp + fn
    compare(
        "vuv_f1_amphion",
        "default_22050",
        2 * tp / den if den else None,
        dict(reference=ref, hypothesis=hyp),
        "Amphion default librosa 22050",
    )
    compare(
        "f0_rmse_amphion",
        "default_22050",
        amphion["f0_rmse"](ref, hyp, kwargs=kw),
        dict(reference=ref, hypothesis=hyp),
        "Amphion default librosa 22050",
    )

    fixtures = args.output.parent / "controls"
    fixtures.mkdir(exist_ok=True)
    waveform, sr = sf.read(rows[-1]["paths"]["ref"], dtype="float64")
    waveform = waveform[: min(len(waveform), sr * 4)]
    n = len(waveform)
    silence = np.zeros(n)
    delayed = np.concatenate([np.zeros(sr // 5), waveform])[:n]
    dropout = waveform.copy()
    dropout[n // 3 : 2 * n // 3] = 0
    noise = np.random.default_rng(20261110).normal(0, 0.1, n)
    specs = {
        "reference": waveform,
        "silence": silence,
        "delay_200ms": delayed,
        "voicing_dropout": dropout,
        "noise": noise,
    }
    for name, value in specs.items():
        sf.write(fixtures / f"{name}.wav", value, sr, subtype="PCM_16")
    base = str(fixtures / "reference.wav")
    ids = ("vuv_f1", "f0_rmse", "vuv_f1_amphion", "f0_rmse_amphion", "log_f0_rmse_espnet")
    for name in specs:
        for metric in ids:
            r = run(metric, reference=base, hypothesis=str(fixtures / f"{name}.wav"))
            entry = dict(control=name, metric=metric, result=r)
            if name == "reference":
                goal = 1.0 if "f1" in metric else 0.0
                entry["passed"] = r["status"] == "ok" and abs(r["value"] - goal) < 1e-10
            elif name == "silence":
                if "f1" in metric:
                    entry["passed"] = r["status"] == "ok" and r["value"] == 0
                elif metric != "f0_rmse_amphion":
                    entry["passed"] = r["value"] is None and r["status"].startswith("undefined")
                else:
                    entry["passed"] = r["status"] == "ok" and r["value"] > 0
            report["controls"].append(entry)
            save()
    for metric in ids:
        r = run(
            metric,
            reference=str(fixtures / "silence.wav"),
            hypothesis=str(fixtures / "silence.wav"),
        )
        report["controls"].append(
            dict(
                control="both_silent",
                metric=metric,
                result=r,
                passed=r["value"] is None and r["status"].startswith("undefined"),
            )
        )
    # Equal sample count is essential in strict profile; truncation must not be implicit.
    r = run("f0_rmse", reference=waveform, hypothesis=waveform[:-100], sample_rate=sr)
    report["controls"].append(
        dict(
            control="length_mismatch",
            metric="f0_rmse",
            result=r,
            passed=r["status"] == "invalid_input",
        )
    )
    r = run("vuv_f1", reference=waveform, hypothesis=np.full(n, np.nan), sample_rate=sr)
    report["controls"].append(
        dict(control="nonfinite", metric="vuv_f1", result=r, passed=r["status"] == "invalid_input")
    )
    # Known-frequency harmonic sources: F1 should remain high when F0 changes.
    # Multiple harmonics make this a voiced-like source, unlike a pure sine.
    t = np.arange(2 * 24000) / 24000
    harmonic_paths = []
    for fundamental in (120, 180):
        signal = sum(
            np.sin(2 * np.pi * fundamental * h * t + 0.13 * h) / (h**1.3) for h in range(1, 13)
        )
        signal *= 0.3 / np.max(np.abs(signal))
        signal += np.random.default_rng(7).normal(0, 1e-5, len(t))
        path = fixtures / f"harmonic_{fundamental}.wav"
        sf.write(path, signal, 24000, subtype="PCM_16")
        harmonic_paths.append(str(path))
    for metric in ("vuv_f1", "f0_rmse"):
        r = run(metric, reference=harmonic_paths[0], hypothesis=harmonic_paths[1])
        passed = r["status"] == "ok" and (
            r["value"] > 0.95 if metric == "vuv_f1" else abs(r["value"] - 60) < 3
        )
        report["controls"].append(
            dict(control="known_120_to_180_Hz_harmonics", metric=metric, result=r, passed=passed)
        )
    # Batch values must be supported with real scorers; retain component counts.
    report["batch"] = {}
    for metric in ids:
        records = [
            dict(id="a", inputs=dict(reference=base, hypothesis=base)),
            dict(
                id="b",
                inputs=dict(reference=base, hypothesis=str(fixtures / "voicing_dropout.wav")),
            ),
        ]
        r = evaluate_batch(metric, records)
        report["batch"][metric] = {k: v for k, v in r.items() if k != "rows"}
    report["summary"] = dict(
        parity_cases=len(report["parity"]),
        parity_passed=sum(r["passed"] for r in report["parity"]),
        asserted_controls=sum("passed" in r for r in report["controls"]),
        controls_passed=sum(r.get("passed", False) for r in report["controls"]),
        max_delta_by_metric={
            metric: max(
                (r["absolute_difference"] or 0 for r in report["parity"] if r["metric"] == metric),
                default=None,
            )
            for metric in ids
        },
    )
    report["complete"] = (
        all(r["passed"] for r in report["parity"])
        and all(r.get("passed", True) for r in report["controls"])
        and all(r["complete"] for r in report["batch"].values())
    )
    save()
    print(json.dumps(report["summary"], indent=2), flush=True)
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
