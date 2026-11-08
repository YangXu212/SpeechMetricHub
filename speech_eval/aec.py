"""Explicit three-signal AECMOS profiles using Microsoft's public scorer."""

PROFILES = {
    "aecmos_16k": ("aecmos_16kHz", 16000, True, "Run_1663915512_Stage_0.onnx"),
    "aecmos_16k_scenarioless": (
        "aecmos_scenarioless_16kHz",
        16000,
        False,
        "Run_1663829550_Stage_0.onnx",
    ),
    "aecmos_48k": ("aecmos_48kHz", 48000, True, "Run_1668423760_Stage_0.onnx"),
}

CHECKPOINT_SHA256 = {
    "aecmos_16k": "f53122f43cb7e5b77ec797e85c8b997cfc2aac8220857c709226d876de8c0a99",
    "aecmos_16k_scenarioless": "b517d8d9ca2f91ea55d15f605a15917c19be5d832868fe115c7c5bc48986dae1",
    "aecmos_48k": "b57bc007046d7230008ad2b802cb378f998ff3d96be074389a4d07533b7d4aaf",
}
SOURCE_SHA256 = "56aef6889be4c2169962e6838d19e9b032925c77d7e841bc1fd9d30b66f5ddec"


def aecmos_family(family, *, hypothesis, farend, microphone, talk_type=None, config=None):
    from .models import model_family

    return model_family(
        family,
        hypothesis=hypothesis,
        reference={"farend": str(farend), "microphone": str(microphone), "talk_type": talk_type},
        config=config,
    )


def aecmos_metric(*, metric, hypothesis, farend, microphone, talk_type=None, config=None):
    from .registry import get_metric
    from .models import select

    spec = get_metric(metric)
    return select(
        aecmos_family(
            spec["family"],
            hypothesis=hypothesis,
            farend=farend,
            microphone=microphone,
            talk_type=talk_type,
            config=config,
        ),
        spec,
    )


def score(request):
    import numpy as np
    import soundfile as sf
    import onnxruntime as ort
    from importlib.metadata import version
    from unittest.mock import patch
    from pathlib import Path
    from .model_worker import require, artifact, source_module

    if ort.__version__ != "1.16.3":
        raise ValueError(
            "AECMOS profiles require ONNX Runtime 1.16.3; newer shape inference rejects the original scenarioless model"
        )

    family, config = request["family"], request["config"]
    model_name, rate, scenario, filename = PROFILES[family]
    signals = request.get("reference")
    if not isinstance(signals, dict) or set(signals) != {"farend", "microphone", "talk_type"}:
        raise ValueError(
            "AECMOS requires farend, microphone, hypothesis and an explicit scenario policy"
        )
    talk = signals["talk_type"]
    if scenario and talk not in ("st", "nst", "dt"):
        raise ValueError("talk_type must be st (far-end), nst (near-end), or dt")
    if not scenario and talk is not None:
        raise ValueError(
            "Scenarioless profile requires talk_type=None; it does not consume markers"
        )
    paths = {
        "farend": signals["farend"],
        "microphone": signals["microphone"],
        "hypothesis": request["hypothesis"],
    }
    audio = {}
    for name, path in paths.items():
        path = Path(path).resolve(strict=True)
        try:
            wave, sr = sf.read(path, dtype="float32")
        except sf.SoundFileError as exc:
            raise ValueError(f"Cannot read {name} audio: {exc}") from exc
        if sr != rate or wave.ndim != 1 or not np.isfinite(wave).all():
            raise ValueError(
                f"{name}: require finite mono {rate} Hz audio; resample/downmix explicitly"
            )
        if not rate <= len(wave) <= 20 * rate:
            raise ValueError(
                f"{name}: require 1 to 20 seconds; longer audio must be explicitly segmented"
            )
        if np.max(np.abs(wave)) > 1:
            raise ValueError(f"{name}: samples outside [-1,1]; no implicit gain normalization")
        audio[name] = wave
    if len({len(w) for w in audio.values()}) != 1:
        raise ValueError("Three signals must have equal lengths; no implicit crop or delay search")
    if not np.any(audio["microphone"]):
        raise ValueError("Silent microphone is outside this evaluation profile")
    if talk in ("st", "dt") and not np.any(audio["farend"]):
        raise ValueError("Declared far-end activity requires a non-silent playback signal")
    source = require(config, "source_file")
    checkpoint = require(config, "checkpoint")
    provenance = {
        k: artifact(v)
        for k, v in {**paths, "source_file": source, "checkpoint": checkpoint}.items()
    }
    if provenance["checkpoint"]["sha256"] != CHECKPOINT_SHA256[family]:
        raise ValueError("Checkpoint does not match the named Microsoft AECMOS profile")
    if provenance["source_file"]["sha256"] != SOURCE_SHA256:
        raise ValueError("Source must be the unmodified speechmos 0.0.1.1 aecmos.py")
    for key, expected in config.get("expected_hashes", {}).items():
        if key not in provenance or provenance[key]["sha256"] != expected:
            raise ValueError(f"Artifact hash mismatch: {key}")
    device = config.get("device", "cpu")
    providers = ["CPUExecutionProvider"]
    if device != "cpu":
        if "CUDAExecutionProvider" not in ort.get_available_providers():
            raise RuntimeError("Requested CUDA is unavailable; refusing silent CPU-only fallback")
        providers = [
            ("CUDAExecutionProvider", {"device_id": 0, "cudnn_conv_algo_search": "DEFAULT"}),
            "CPUExecutionProvider",
        ]
    options = ort.SessionOptions()
    options.use_deterministic_compute = True
    options.intra_op_num_threads = config.get("threads", 2)
    options.inter_op_num_threads = 1
    if config.get("profiling_output"):
        options.enable_profiling = True
        options.profile_file_prefix = str(config["profiling_output"])
    session = ort.InferenceSession(checkpoint, sess_options=options, providers=providers)
    session.disable_fallback()
    if device != "cpu" and "CUDAExecutionProvider" not in session.get_providers():
        raise RuntimeError("CUDA session initialization failed; refusing CPU-only scoring")
    upstream = source_module(source, "speechmetrichub_official_aecmos")
    # Redirect only session construction. All frontend, scenario markers and output heads are upstream.
    with patch.object(upstream.ort, "InferenceSession", return_value=session):
        scorer = upstream.AECMOS(model_name)
    echo, deg = scorer._get_mos(talk, audio["farend"], audio["microphone"], audio["hypothesis"])
    if not np.isfinite([echo, deg]).all():
        raise ArithmeticError("AECMOS returned nonfinite scores")
    details = {"samples": len(audio["hypothesis"]), "seconds": len(audio["hypothesis"]) / rate}
    if config.get("profiling_output"):
        details["onnx_profile"] = session.end_profiling()
    return {
        "status": "ok",
        "values": {"echo_mos": float(echo), "deg_mos": float(deg)},
        "details": details,
        "provenance": provenance,
        "backend": {p: version(p) for p in ("numpy", "scipy", "librosa", "soundfile")}
        | {"onnxruntime": ort.__version__, "providers": session.get_providers()},
        "protocol": {
            "profile": "aecmos-microsoft-v1",
            "family": family,
            "model_name": model_name,
            "sample_rate": rate,
            "talk_type": talk,
            "minimum_seconds": 1,
            "maximum_seconds": 20,
            "channel_policy": "strict_mono",
            "length_policy": "strict_equal",
            "resampling": "none",
            "gain_normalization": "none",
            "delay_alignment": "none",
            "long_audio_policy": "reject; segment explicitly",
            "onnx_math_mode": "float32; NVIDIA_TF32_OVERRIDE=0 in isolated worker",
            "deterministic_compute": True,
            "cudnn_conv_algo_search": "DEFAULT",
            "cublas_workspace_config": ":4096:8",
            "artifact_hashes": {k: provenance[k]["sha256"] for k in ("source_file", "checkpoint")},
        },
    }
