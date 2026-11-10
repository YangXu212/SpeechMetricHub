"""Isolated, explicit model execution; no downloads during scoring.

Use ``evaluate`` to request several heads of one model with a single forward pass.
Model code and checkpoints are trusted local artifacts supplied in config.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def model_family(family, *, hypothesis, reference=None, config=None):
    config = dict(config or {})
    device = config.get("device", "cpu")
    if not isinstance(device, str) or (
        device != "cpu" and not (device.startswith("cuda:") and device[5:].isdigit())
    ):
        raise ValueError("device must be cpu or an explicit cuda:N")
    timeout = config.get("timeout", 600)
    if (
        isinstance(timeout, bool)
        or not isinstance(timeout, (int, float))
        or not math.isfinite(timeout)
        or timeout <= 0
    ):
        raise ValueError("timeout must be finite and positive")
    threads = config.get("threads", 2)
    if isinstance(threads, bool) or not isinstance(threads, int) or not 1 <= threads <= 64:
        raise ValueError("threads must be an integer from 1 to 64")
    env = os.environ.copy()
    if family.startswith("aecmos_"):
        env["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
        env["NVIDIA_TF32_OVERRIDE"] = "0"
    if (
        family.startswith("aecmos_")
        and sys.platform == "linux"
        and (
            not config.get("python")
            or Path(config["python"]).absolute() == Path(sys.executable).absolute()
        )
    ):
        from importlib.metadata import distribution, PackageNotFoundError

        libraries = []
        for package, folder in (
            ("nvidia-cublas-cu11", "cublas"),
            ("nvidia-cudnn-cu11", "cudnn"),
            ("nvidia-cuda-runtime-cu11", "cuda_runtime"),
            ("nvidia-cuda-nvrtc-cu11", "cuda_nvrtc"),
            ("nvidia-cufft-cu11", "cufft"),
            ("nvidia-curand-cu11", "curand"),
        ):
            try:
                path = distribution(package).locate_file(f"nvidia/{folder}/lib")
                if path.is_dir():
                    libraries.append(str(path))
            except PackageNotFoundError:
                pass
        if libraries:
            env["LD_LIBRARY_PATH"] = os.pathsep.join(libraries + [env.get("LD_LIBRARY_PATH", "")])
    env.update(
        OMP_NUM_THREADS=str(threads),
        MKL_NUM_THREADS=str(threads),
        OPENBLAS_NUM_THREADS=str(threads),
        NUMEXPR_NUM_THREADS=str(threads),
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
    )
    env["CUDA_VISIBLE_DEVICES"] = "" if device == "cpu" else device[5:]
    config["device"] = "cpu" if device == "cpu" else "cuda:0"
    env["PYTHONPATH"] = (
        str(Path(__file__).resolve().parent.parent) + os.pathsep + env.get("PYTHONPATH", "")
    )
    if config.get("trusted_checkpoint"):
        env["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = "1"
    request = dict(family=family, hypothesis=str(hypothesis), reference=reference, config=config)
    if isinstance(reference, Path):
        request["reference"] = str(reference)
    with tempfile.TemporaryDirectory(prefix="speech_eval_") as directory:
        inp, out = Path(directory) / "input.json", Path(directory) / "output.json"
        inp.write_text(json.dumps(request), encoding="utf-8")
        try:
            process = subprocess.run(
                [
                    config.get("python", sys.executable),
                    "-m",
                    "speech_eval.model_worker",
                    str(inp),
                    str(out),
                ],
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "values": {},
                "reason": "Model worker exceeded configured timeout",
            }
        except OSError as exc:
            return {"status": "dependency_unavailable", "values": {}, "reason": str(exc)}
        if not out.exists():
            return {
                "status": "backend_error",
                "values": {},
                "reason": process.stderr[-5000:] or f"Worker exited {process.returncode}",
            }
        result = json.loads(out.read_text(encoding="utf-8"))
        result["execution"] = {"device": device, "threads": threads, "isolated_process": True}
        return result


def model_metric(*, metric, hypothesis, reference=None, config=None):
    from .registry import get_metric

    spec = get_metric(metric)
    result = model_family(spec["family"], hypothesis=hypothesis, reference=reference, config=config)
    return select(result, spec)


def select(result, spec):
    selected = {
        **result,
        "metric": spec["id"],
        "value": result.get("values", {}).get(spec["output"]),
        "value_unit": spec["unit"],
        "direction": spec["direction"],
    }
    if selected["status"] == "ok" and selected["value"] is None:
        selected.update(status="backend_error", reason=f"Missing declared output: {spec['output']}")
    if spec["id"] == "lps_phone" and "protocol" in selected:
        selected["protocol"] = {
            **selected["protocol"],
            "tokenization": "space-delimited decoded phonemes; URGENT 2026 LPS",
        }
    if spec["family"] in ("whisper_wer", "whisper_dwer"):
        selected.update(
            {
                k: result.get("details", {})[k]
                for k in ("N", "S", "D", "I", "errors")
                if k in result.get("details", {})
            }
        )
    return selected


def evaluate(metrics, *, hypothesis, reference=None, configs=None, **inputs):
    """Evaluate multiple metrics, sharing each model's multi-head forward pass.

    configs maps family names to deployment settings. Non-model inputs, e.g.
    sample_rate, are passed only to the non-model adapters.
    """
    from .registry import get_metric, run

    configs = configs or {}
    metrics = list(metrics)
    cache, results = {}, {}
    for name in metrics:
        spec = get_metric(name)
        if spec.get("adapter") == "speech_eval.pitch:pitch_metric":
            if "pitch" not in cache:
                from .pitch import evaluate_pitch

                pitch_names = [
                    n
                    for n in metrics
                    if get_metric(n).get("adapter") == "speech_eval.pitch:pitch_metric"
                ]
                try:
                    cache["pitch"] = evaluate_pitch(
                        pitch_names, reference=reference, hypothesis=hypothesis, **inputs
                    )
                except ImportError:
                    # Preserve registry dependency_unavailable results for partial installs.
                    cache["pitch"] = {
                        n: run(n, reference=reference, hypothesis=hypothesis, **inputs)
                        for n in pitch_names
                    }
            results[name] = cache["pitch"][name]
        elif spec.get("adapter") in (
            "speech_eval.models:model_metric",
            "speech_eval.aec:aecmos_metric",
        ):
            family = spec["family"]
            if family not in cache:
                if spec["adapter"] == "speech_eval.aec:aecmos_metric":
                    from .aec import aecmos_family

                    cache[family] = aecmos_family(
                        family,
                        hypothesis=hypothesis,
                        farend=inputs.get("farend"),
                        microphone=inputs.get("microphone"),
                        talk_type=inputs.get("talk_type"),
                        config=configs.get(family),
                    )
                else:
                    cache[family] = model_family(
                        family,
                        hypothesis=hypothesis,
                        reference=reference,
                        config=configs.get(family),
                    )
            results[name] = select(cache[family], spec)
        else:
            non_model_inputs = {
                key: value
                for key, value in inputs.items()
                if key not in ("farend", "microphone", "talk_type")
            }
            results[name] = run(
                name, hypothesis=hypothesis, reference=reference, **non_model_inputs
            )
    return results
