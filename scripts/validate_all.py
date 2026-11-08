"""Call every registered metric ID independently in one interpreter/environment.

Requires explicitly provisioned model configs and real speech fixtures. This is
runtime integration coverage, not a population/model-quality benchmark.
"""

import argparse
from importlib import metadata
import json
import math
from pathlib import Path
import platform
import sys
import time

import numpy as np
import soundfile as sf

from speechmetrichub import list_metrics, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--fixtures", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", choices=("core", "models", "all"), default="all")
    parser.add_argument("--only", nargs="+")
    args = parser.parse_args()
    configs = json.loads(Path(args.config).read_text())
    fixtures = Path(args.fixtures)
    reference, rate = sf.read(fixtures / "ref.wav", dtype="float64")
    noisy, noisy_rate = sf.read(fixtures / "noisy.wav", dtype="float64")
    auxiliary, auxiliary_rate = sf.read(fixtures / "aux.wav", dtype="float64")
    mixture, mixture_rate = sf.read(fixtures / "mix.wav", dtype="float64")
    assert rate == noisy_rate == auxiliary_rate == mixture_rate == 16000
    segments = [
        {"speaker": "a", "start": 0.0, "end": 2.0, "text": "one two three"},
        {"speaker": "b", "start": 2.0, "end": 4.0, "text": "four five six"},
    ]
    hypothesis = [
        {"speaker": "x", "start": 0.0, "end": 2.0, "text": "one too three"},
        {"speaker": "y", "start": 2.0, "end": 4.0, "text": "four six"},
    ]
    rng = np.random.default_rng(20261108)
    length = min(len(reference), len(auxiliary))
    sources = np.stack([reference[:length], auxiliary[:length]])
    estimates = sources[::-1] + rng.normal(0, 0.01, sources.shape)
    output = Path(args.output)
    report = json.loads(output.read_text()) if output.exists() else {"rows": {}}
    report.update(
        schema="speechmetrichub-all-interfaces-v1",
        python=platform.python_version(),
        interpreter=sys.executable,
        packages={p.metadata["Name"]: p.version for p in metadata.distributions()},
        scope="Independent run() call per registry ID, including aliases; integration fixtures only",
    )
    specs = list_metrics()
    if args.only and set(args.only) - {s["id"] for s in specs}:
        parser.error("Unknown metric ID in --only")
    for spec in specs:
        name, family = spec["id"], spec.get("family")
        if args.only and name not in args.only:
            continue
        if args.mode == "core" and family or args.mode == "models" and not family:
            continue
        start = time.perf_counter()
        try:
            if family:
                config = configs[family]
                if config.get("python"):
                    raise ValueError(
                        "Single-environment validation prohibits alternate interpreters"
                    )
                if family.startswith("aecmos_"):
                    sample_rate = 48000 if family == "aecmos_48k" else 16000
                    folder = fixtures / "aec" / f"dt-{sample_rate}"
                    inputs = {
                        key: str(folder / (key + ".wav"))
                        for key in ("farend", "microphone", "hypothesis")
                    }
                    inputs.update(
                        config=config, talk_type=None if "scenarioless" in family else "dt"
                    )
                else:
                    ref = (
                        "one two three four five six"
                        if family == "whisper_wer"
                        else str(fixtures / "ref.wav")
                    )
                    if (
                        family.startswith("scoreq_")
                        and config.get("reference_kind") == "nonmatching"
                    ):
                        ref = str(fixtures / "aux.wav")
                    inputs = dict(
                        hypothesis=str(fixtures / "noisy.wav"), reference=ref, config=config
                    )
            elif name in ("eer", "min_dcf"):
                inputs = dict(
                    scores=[0.9, 0.8, 0.7, 0.7, 0.5, 0.4, 0.3, 0.1], labels=[1, 1, 0, 1, 0, 1, 0, 0]
                )
                if name == "min_dcf":
                    inputs["p_target"] = 0.01
            elif name == "erle":
                inputs = dict(
                    reference=reference,
                    hypothesis=reference * 0.1,
                    sample_rate=rate,
                    farend_only_regions=[[0, len(reference) / rate]],
                    signal_definition="isolated_echo",
                )
            elif name in ("speaker_count", "der", "jer") or name.startswith("vad_"):
                inputs = dict(reference=segments, hypothesis=hypothesis)
                if name != "speaker_count":
                    inputs.update(uem=[[0, 6]], reference_is_speech_activity=True)
            elif spec["category"] == "recognition":
                inputs = dict(reference=segments, hypothesis=hypothesis)
                if name.startswith("ts_"):
                    inputs = dict(reference="one two three", hypothesis="one too three")
            elif name.startswith("bss_"):
                inputs = dict(reference=sources, hypothesis=estimates)
            elif spec["category"] == "rating_agreement":
                inputs = dict(reference=[1, 2, 3, 4], hypothesis=[1.1, 2.3, 2.9, 4.1])
            else:
                inputs = dict(reference=reference, hypothesis=noisy, sample_rate=rate)
                if name == "si_sdri":
                    inputs["mixture"] = mixture
            result = run(name, **inputs)
            passed = (
                result.get("status") == "ok"
                and result.get("value") is not None
                and math.isfinite(result["value"])
            )
        except Exception as exc:
            result = dict(status="exception", value=None, reason=f"{type(exc).__name__}: {exc}")
            passed = False
        report["rows"][name] = dict(
            passed=passed,
            family=family,
            alias_of=spec.get("alias_of"),
            elapsed_seconds=time.perf_counter() - start,
            result=result,
        )
        report["expected"] = len(specs)
        report["attempted"] = len(report["rows"])
        report["passed"] = sum(row["passed"] for row in report["rows"].values())
        report["complete"] = report["expected"] == report["attempted"] == report["passed"]
        output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        print(name, result.get("status"), result.get("value"), result.get("reason", ""), flush=True)
    selected = [
        s["id"]
        for s in specs
        if (not args.only or s["id"] in args.only)
        and (args.mode == "all" or (args.mode == "models") == bool(s.get("family")))
    ]
    return 0 if all(report["rows"][name]["passed"] for name in selected) else 2


if __name__ == "__main__":
    raise SystemExit(main())
