"""Real inference validation, separate from lightweight CI. See docs/AEC_VERIFICATION.md."""

import argparse
import copy
import json
from pathlib import Path
import tempfile

import numpy as np
import soundfile as sf

from speechmetrichub import evaluate, run
from speech_eval.aec import PROFILES
from speech_eval.model_worker import source_module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--fixtures", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    configs = json.loads(Path(args.config).read_text())
    fixtures = Path(args.fixtures)
    checks = []
    rows = []

    def check(name, passed, **details):
        checks.append(dict(name=name, passed=bool(passed), **details))
        print(name, "PASS" if passed else "FAIL", flush=True)

    with tempfile.TemporaryDirectory() as temporary:
        tmp = Path(temporary)
        for family, (model_name, rate, has_marker, _) in PROFILES.items():
            ids = [family + "_echo", family + "_deg"]
            upstream = source_module(configs[family]["source_file"], "official_aec_validation")
            # Upstream CPU reference, unchanged file loading avoided by passing float32 arrays.
            import onnxruntime as ort
            from unittest.mock import patch

            options = ort.SessionOptions()
            options.intra_op_num_threads = 2
            session = ort.InferenceSession(
                configs[family]["checkpoint"],
                sess_options=options,
                providers=["CPUExecutionProvider"],
            )
            with patch.object(upstream.ort, "InferenceSession", return_value=session):
                official = upstream.AECMOS(model_name)
            for talk in ("st", "nst", "dt"):
                folder = fixtures / f"{talk}-{rate}"
                paths = {
                    key: str(folder / (key + ".wav"))
                    for key in ("farend", "microphone", "hypothesis")
                }
                marker = talk if has_marker else None
                arrays = [
                    sf.read(paths[key], dtype="float32")[0]
                    for key in ("farend", "microphone", "hypothesis")
                ]
                gold = official._get_mos(marker, *arrays)
                cpu_configs = copy.deepcopy(configs)
                cpu_configs[family]["device"] = "cpu"
                cpu = evaluate(ids, **paths, talk_type=marker, configs=cpu_configs)
                gpu_configs = copy.deepcopy(configs)
                gpu_configs[family]["profiling_output"] = str(tmp / f"{family}-{talk}")
                gpu = evaluate(ids, **paths, talk_type=marker, configs=gpu_configs)
                for index, name in enumerate(ids):
                    a, b = cpu[name], gpu[name]
                    ok = a["status"] == b["status"] == "ok"
                    check(
                        f"{name}/{talk}/cpu_gpu_upstream",
                        ok
                        and abs(a["value"] - gold[index]) < 1e-6
                        and abs(b["value"] - gold[index]) < 1e-4,
                        cpu=a.get("value"),
                        gpu=b.get("value"),
                        upstream=gold[index],
                        reason=b.get("reason", a.get("reason")),
                    )
                    rows.append(
                        {
                            "metric": name,
                            "scenario": talk,
                            "model_marker": marker,
                            "cpu": a,
                            "gpu": b,
                            "upstream_cpu": gold[index],
                        }
                    )
                if gpu[ids[0]]["status"] == "ok":
                    trace = json.loads(Path(gpu[ids[0]]["details"]["onnx_profile"]).read_text())
                    nodes = [
                        event
                        for event in trace
                        if event.get("args", {}).get("provider") == "CUDAExecutionProvider"
                    ]
                    check(
                        f"{family}/{talk}/actual_cuda_kernels",
                        len(nodes) > 0,
                        kernel_events=len(nodes),
                    )
                if talk == "dt":
                    repeat = evaluate(ids, **paths, talk_type=marker, configs=configs)
                    again = evaluate(ids, **paths, talk_type=marker, configs=configs)
                    check(
                        f"{family}/profiling_on_off",
                        all(
                            repeat[name]["status"] == "ok"
                            and abs(repeat[name]["value"] - gpu[name]["value"]) < 1e-6
                            for name in ids
                        ),
                        absolute_deltas={
                            name: abs(repeat[name]["value"] - gpu[name]["value"]) for name in ids
                        },
                        tolerance=1e-6,
                    )
                    check(
                        f"{family}/repeat",
                        all(
                            again[name]["status"] == "ok"
                            and abs(again[name]["value"] - repeat[name]["value"]) < 1e-6
                            for name in ids
                        ),
                        absolute_deltas={
                            name: abs(again[name]["value"] - repeat[name]["value"]) for name in ids
                        },
                        tolerance=1e-6,
                    )
            # Invalid-input controls for every profile, using the last (dt) triplet.
            for kind, wave, sr in (
                ("wrong_rate", arrays[2], 24000),
                ("short", arrays[2][: rate // 2], rate),
                ("long", np.tile(arrays[2], 3), rate),
                ("stereo", np.stack([arrays[2]] * 2, axis=1), rate),
                ("nonfinite", np.full(rate, np.nan, dtype=np.float32), rate),
                ("overrange", np.full(rate, 1.1, dtype=np.float32), rate),
                ("unequal_length", arrays[2][:-1], rate),
            ):
                path = tmp / f"{family}-{kind}.wav"
                sf.write(path, wave, sr, subtype="FLOAT")
                result = run(
                    ids[0],
                    **{**paths, "hypothesis": str(path)},
                    talk_type=marker,
                    config=configs[family],
                )
                check(
                    f"{family}/reject_{kind}",
                    result["status"] == "invalid_input",
                    status=result["status"],
                )
            for kind, overrides, config in (
                ("missing_file", {"hypothesis": str(tmp / "missing.wav")}, configs[family]),
                ("invalid_marker", {"talk_type": None if has_marker else "dt"}, configs[family]),
                ("hash_mismatch", {}, {**configs[family], "expected_hashes": {"checkpoint": "0"}}),
                (
                    "wrong_profile",
                    {},
                    {
                        **configs[family],
                        "checkpoint": configs["aecmos_48k" if rate == 16000 else "aecmos_16k"][
                            "checkpoint"
                        ],
                    },
                ),
            ):
                result = run(ids[0], **{**paths, "talk_type": marker, **overrides}, config=config)
                check(
                    f"{family}/reject_{kind}",
                    result["status"] == "invalid_input",
                    status=result["status"],
                )
            # Zero enhanced output is meaningful (over-suppression), and must remain scoreable.
            zero = tmp / f"zero-{rate}.wav"
            sf.write(zero, np.zeros_like(arrays[2]), rate, subtype="FLOAT")
            result = run(
                ids[0],
                **{**paths, "hypothesis": str(zero), "farend": str(zero)},
                talk_type="nst" if has_marker else None,
                config=configs[family],
            )
            check(f"{family}/nearend_silent_farend_and_enhanced", result["status"] == "ok")
        # Explicitly masked real microphone baseline plus a controlled residual, not a model benchmark.
        mic = sf.read(fixtures / "st-16000/microphone.wav", dtype="float64")[0]
        settings = dict(
            reference=mic,
            sample_rate=16000,
            farend_only_regions=[[0, 10]],
            signal_definition="microphone_farend_only",
        )
        for gain, expected in ((1, 0), (0.1, 20)):
            result = run("erle", hypothesis=mic * gain, **settings)
            check(
                f"erle/real_microphone_gain_{gain}",
                result["status"] == "ok" and abs(result["value"] - expected) < 1e-10,
                value=result["value"],
            )
        config = {**configs["aecmos_16k"], "device": "cuda:999"}
        paths = {
            key: str(fixtures / "dt-16000" / (key + ".wav"))
            for key in ("farend", "microphone", "hypothesis")
        }
        result = run("aecmos_16k_echo", **paths, talk_type="dt", config=config)
        check("cuda_unavailable_no_cpu_fallback", result["status"] != "ok", status=result["status"])

    def sanitize(value):
        if isinstance(value, dict):
            return {
                key: sanitize(val)
                for key, val in value.items()
                if key not in ("traceback", "onnx_profile")
            }
        if isinstance(value, list):
            return [sanitize(val) for val in value]
        if isinstance(value, str) and value.startswith("/"):
            return Path(value).name
        return value

    report = dict(
        release="0.5.0",
        passed=all(c["passed"] for c in checks),
        checks=checks,
        rows=rows,
        scope="Three real AEC Challenge scenarios, ten-second passthrough baseline; 48k is explicitly resampled interface coverage, not native fullband benchmark",
    )
    Path(args.output).write_text(json.dumps(sanitize(report), indent=2, allow_nan=False) + "\n")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
