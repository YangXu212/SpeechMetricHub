# Amphion-derived recipe: Copyright (c) 2023 Amphion, MIT License.
# ESPnet-derived recipe: Copyright 2021 Wen-Chin Huang and Tomoki Hayashi,
# Apache License 2.0. Full notices and modifications are in THIRD_PARTY.md.
"""Pitch/voicing evaluation with named, non-interchangeable protocols.

The strict profile is defined by SpeechMetricHub. Amphion and ESPnet profiles
adapt their published recipes, delegating feature extraction/alignment to the
original libraries. See docs/PITCH.md and THIRD_PARTY.md for source/license notes.
No model weights or GPU are required. Imports remain lazy.
"""

from importlib.metadata import version
from pathlib import Path
import hashlib
import math


AMPHION_REVISION = "26f6883110181f1dbfe95c70a7c7dbaf4de5f42a"
ESPNET_REVISION = "c573dfed21a3d64ce491a6f53748cc6b596097e5"
PITCH_METRICS = {
    "vuv_f1": "world_aligned_v1",
    "f0_rmse": "world_aligned_v1",
    "vuv_f1_amphion": "amphion_v1",
    "f0_rmse_amphion": "amphion_v1",
    "log_f0_rmse_espnet": "espnet_v1",
}


def _counts(reference, hypothesis, *, common_only=True, logarithmic=False):
    """Sufficient statistics on already aligned F0 contours (0 = unvoiced)."""
    import numpy as np

    a, b = np.asarray(reference, dtype=np.float64), np.asarray(hypothesis, dtype=np.float64)
    if a.ndim != 1 or a.shape != b.shape or not a.size:
        raise ValueError("Require nonempty equally sized 1D F0 contours")
    if not np.isfinite(a).all() or not np.isfinite(b).all() or np.any(a < 0) or np.any(b < 0):
        raise ValueError("F0 must be finite and nonnegative, with 0 marking unvoiced")
    av, bv = a > 0, b > 0
    common = av & bv
    mask = common if common_only else np.ones(a.shape, dtype=bool)
    x, y = a[mask], b[mask]
    if logarithmic:
        x, y = np.log(x), np.log(y)
    squared = float(np.sum((x - y) ** 2, dtype=np.float64))
    tp, fp, fn, tn = [int(np.count_nonzero(z)) for z in (common, ~av & bv, av & ~bv, ~av & ~bv)]
    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "TN": tn,
        "squared_error_sum": squared,
        "scored_frames": int(mask.sum()),
        "total_frames": len(a),
        "reference_voiced_frames": int(av.sum()),
        "hypothesis_voiced_frames": int(bv.sum()),
        "common_voiced_frames": tp,
        "common_voiced_fraction": tp / len(a),
        "reference_voiced_coverage": tp / int(av.sum()) if av.any() else None,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "vuv_error_rate": (fp + fn) / len(a),
    }


def _positive(value, name, *, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a positive {'integer' if integer else 'number'}")
    if not math.isfinite(value) or value <= 0 or (integer and not isinstance(value, int)):
        raise ValueError(f"Invalid {name}")
    return value


def _provenance(value):
    if isinstance(value, (str, Path)):
        path = Path(value)
        return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return {"input": "in_memory_waveform"}


def _mono(value):
    import numpy as np

    wave = np.asarray(value)
    if wave.ndim != 1 or not wave.size:
        raise ValueError("Require a nonempty mono waveform")
    if not np.isfinite(wave).all():
        raise ValueError("Waveform contains nonfinite samples")
    return wave


def _native_pair(reference, hypothesis, sample_rate, *, int16=False):
    import numpy as np
    import soundfile as sf

    arrays, rates = [], []
    for value in (reference, hypothesis):
        if isinstance(value, (str, Path)):
            if int16:
                # Reject corrupt FLOAT files before int16 decoding can hide NaN/Inf.
                # Score the original int16 decoder output to retain ESPnet parity.
                check, _ = sf.read(value, dtype="float64")
                _mono(check)
            wave, rate = sf.read(value, dtype="int16" if int16 else "float64")
        else:
            if int16:
                raise ValueError("ESPnet compatibility requires audio file paths (int16 decoding)")
            wave, rate = np.asarray(value), sample_rate
            if wave.dtype.kind != "f":
                raise ValueError("In-memory audio must use floating-point normalized samples")
        arrays.append(_mono(wave).astype(np.float64))
        rates.append(rate)
    rate = sample_rate if sample_rate is not None else rates[0]
    _positive(rate, "sample_rate", integer=True)
    if rate < 16000:
        raise ValueError("WORLD profile requires sample_rate >= 16000; resample explicitly")
    if any(r != rate for r in rates):
        raise ValueError("File sample rates must match each other and declared sample_rate")
    return arrays, rate


def _prepare(profile, reference, hypothesis, sample_rate=None, **options):
    import numpy as np

    protocol = {
        "profile": profile,
        "gain_normalization": "none",
        "silence_removal": False,
        "voicing_definition": "extracted_f0_greater_than_zero",
        "empty_score_policy": "undefined_result_null",
    }
    backend = {"numpy": version("numpy"), "soundfile": version("soundfile")}
    params = dict(options)
    default_min, default_max = (
        (40, 800)
        if profile == "espnet_v1"
        else (50, 1100)
        if profile == "amphion_v1"
        else (50, 800)
    )
    f0_min = _positive(params.pop("f0_min", default_min), "f0_min")
    f0_max = _positive(params.pop("f0_max", default_max), "f0_max")
    if f0_min >= f0_max:
        raise ValueError("f0_min must be less than f0_max")
    protocol.update(f0_min=f0_min, f0_max=f0_max)
    if profile == "amphion_v1":
        import librosa
        import parselmouth

        hop = _positive(params.pop("hop_length", 256), "hop_length", integer=True)
        method = params.pop("method", "cut")
        need_mean = params.pop("need_mean", False)
        if need_mean is not False:
            raise ValueError(
                "This Hz profile requires need_mean=False; median-centered cents are a different metric"
            )
        if method not in ("cut", "dtw"):
            raise ValueError("Amphion method must be cut or dtw")
        rate = 22050 if sample_rate is None else _positive(sample_rate, "sample_rate", integer=True)
        if f0_max >= rate / 2:
            raise ValueError("f0_max must be below Nyquist")
        if params:
            raise ValueError(f"Unsupported parameters: {sorted(params)}")
        waves = []
        for value in (reference, hypothesis):
            if not isinstance(value, (str, Path)):
                raise ValueError(
                    "Amphion compatibility requires file paths to preserve librosa loading"
                )
            wave, _ = librosa.load(
                value, sr=rate, mono=True, dtype=np.float32, res_type="kaiser_best"
            )
            waves.append(_mono(wave))
        protocol.update(
            sample_rate=rate,
            extractor="praat_autocorrelation",
            hop_length=hop,
            voicing_threshold=0.6,
            channel_policy="librosa_mono_downmix",
            resampling="librosa_kaiser_best",
            waveform_scale="librosa_float32",
            alignment="truncate_f0_to_shorter" if method == "cut" else "librosa_dtw_on_f0",
            need_mean=False,
            rmse_mask="all_aligned_frames_including_unvoiced_zero",
            upstream_revision=AMPHION_REVISION,
        )
        backend.update({p: version(p) for p in ("librosa", "praat-parselmouth", "resampy")})
        contours = [
            parselmouth.Sound(wave, rate)
            .to_pitch_ac(
                time_step=hop / rate,
                voicing_threshold=0.6,
                pitch_floor=f0_min,
                pitch_ceiling=f0_max,
            )
            .selected_array["frequency"]
            for wave in waves
        ]
        original_lengths = [len(f) for f in contours]
        if min(original_lengths) <= 1:
            raise ValueError("At least two extracted pitch frames are required")
        if method == "cut":
            n = min(original_lengths)
            a, b = [f[:n] for f in contours]
        else:
            if original_lengths[0] * original_lengths[1] > 25_000_000:
                raise ValueError(
                    "Exact Amphion DTW exceeds 25 million cells; evaluate shorter utterances"
                )
            _, path = librosa.sequence.dtw(*contours, backtrack=True)
            a, b = contours[0][path[:, 0]], contours[1][path[:, 1]]
        stats = _counts(a, b, common_only=False)
    else:
        import pyworld

        waves, rate = _native_pair(reference, hypothesis, sample_rate, int16=profile == "espnet_v1")
        if f0_max >= rate / 2:
            raise ValueError("f0_max must be below Nyquist")
        if min(map(len, waves)) / rate < max(0.1, 3 / f0_min):
            raise ValueError("Audio must be at least 100 ms and three minimum-F0 periods long")
        protocol.update(
            sample_rate=rate,
            extractor="world_harvest",
            channel_policy="strict_mono",
            resampling="none",
        )
        backend["pyworld"] = version("pyworld")
        if profile == "world_aligned_v1":
            period = _positive(params.pop("frame_period", 5.0), "frame_period")
            if period < 1 or period > 100:
                raise ValueError("frame_period must be between 1 and 100 ms")
            if params:
                raise ValueError(f"Unsupported parameters: {sorted(params)}")
            if waves[0].shape != waves[1].shape:
                raise ValueError(
                    "Aligned WORLD profile requires equal sample counts; no implicit crop"
                )
            protocol.update(
                frame_period_ms=period,
                alignment="original_time_axis",
                length_policy="strict_equal",
                waveform_scale="float64_original_amplitude",
                rmse_mask="both_voiced",
            )
            contours = [
                pyworld.harvest(wave, rate, f0_floor=f0_min, f0_ceil=f0_max, frame_period=period)[0]
                for wave in waves
            ]
            original_lengths = [len(f) for f in contours]
            stats = _counts(*contours)
        elif profile == "espnet_v1":
            import pysptk
            from fastdtw import fastdtw
            from scipy.spatial.distance import euclidean

            n_fft = _positive(params.pop("n_fft", 1024), "n_fft", integer=True)
            shift = _positive(params.pop("n_shift", 256), "n_shift", integer=True)
            order, alpha = params.pop("mcep_dim", None), params.pop("mcep_alpha", None)
            if params:
                raise ValueError(f"Unsupported parameters: {sorted(params)}")
            if n_fft < 128 or n_fft & (n_fft - 1):
                raise ValueError("n_fft must be a power of two >= 128")
            if order is None or alpha is None:
                settings = {
                    16000: (23, 0.42),
                    22050: (34, 0.45),
                    24000: (34, 0.46),
                    44100: (39, 0.53),
                    48000: (39, 0.55),
                }
                if rate not in settings:
                    raise ValueError("No ESPnet automatic mcep parameters for this sample rate")
                order, alpha = settings[rate]
            _positive(order, "mcep_dim", integer=True)
            if order >= n_fft // 2 or not isinstance(alpha, (int, float)) or not -1 < alpha < 1:
                raise ValueError("Invalid mcep order or alpha")
            contours, features = [], []
            for wave in waves:
                f0, times = pyworld.harvest(
                    wave, rate, f0_floor=f0_min, f0_ceil=f0_max, frame_period=shift / rate * 1000
                )
                spectrum = pyworld.cheaptrick(wave, f0, times, rate, fft_size=n_fft)
                contours.append(f0)
                features.append(pysptk.sp2mc(spectrum, order, alpha))
            # Upstream calls fastdtw(generated, ground_truth), which matters for ties.
            _, path = fastdtw(features[1], features[0], radius=1, dist=euclidean)
            indices = np.asarray(path)
            a, b = contours[0][indices[:, 1]], contours[1][indices[:, 0]]
            original_lengths = [len(f) for f in contours]
            stats = _counts(a, b, logarithmic=True)
            protocol.update(
                n_fft=n_fft,
                n_shift=shift,
                frame_period_ms=shift / rate * 1000,
                mcep_dim=order,
                mcep_alpha=alpha,
                waveform_scale="soundfile_int16_to_float64",
                alignment="fastdtw_radius1_euclidean_mcep_all_coefficients",
                alignment_argument_order="hypothesis_reference",
                rmse_mask="both_voiced",
                logarithm="natural",
                upstream_revision=ESPNET_REVISION,
            )
            backend.update({p: version(p) for p in ("pysptk", "fastdtw", "scipy")})
        else:
            raise ValueError(f"Unknown pitch profile: {profile}")
    stats.update(
        reference_extracted_frames=original_lengths[0],
        hypothesis_extracted_frames=original_lengths[1],
    )
    return {
        "protocol": protocol,
        "backend": backend,
        "details": stats,
        "provenance": {"reference": _provenance(reference), "hypothesis": _provenance(hypothesis)},
    }


def _select(metric, common):
    result = {**common, "metric": metric}
    if "status" in common:
        return result
    data = common["details"]
    is_f1 = metric.startswith("vuv_f1")
    denominator = 2 * data["TP"] + data["FP"] + data["FN"] if is_f1 else data["scored_frames"]
    value = (
        (
            2 * data["TP"] / denominator
            if is_f1
            else math.sqrt(data["squared_error_sum"] / denominator)
        )
        if denominator
        else None
    )
    if metric == "f0_rmse_amphion" and not (
        data["reference_voiced_frames"] + data["hypothesis_voiced_frames"]
    ):
        value = None
    method = (
        "micro_confusion_counts"
        if is_f1
        else ("micro_squared_error_over_frames" if metric == "f0_rmse" else "utterance_macro")
    )
    return {
        **result,
        "status": "ok" if value is not None else "undefined_result",
        "value": value,
        "value_unit": "ratio" if is_f1 else "ln_Hz_ratio" if metric.startswith("log_") else "Hz",
        "direction": "higher_is_better" if is_f1 else "lower_is_better",
        "protocol": {**common["protocol"], "aggregation": method},
        **(
            {"reason": "No defined voiced support; no fabricated perfect score"}
            if value is None
            else {}
        ),
    }


def evaluate_pitch(metrics, *, reference, hypothesis, sample_rate=None, **inputs):
    """Score requested pitch metrics, extracting a pair once per distinct profile."""
    cache, results = {}, {}
    for metric in metrics:
        if metric not in PITCH_METRICS:
            raise ValueError(f"Unknown pitch metric: {metric}")
        profile = PITCH_METRICS[metric]
        if profile not in cache:
            try:
                cache[profile] = _prepare(profile, reference, hypothesis, sample_rate, **inputs)
            except ImportError:
                raise
            except (ValueError, TypeError, OSError, RuntimeError) as exc:
                cache[profile] = {
                    "status": "invalid_input",
                    "value": None,
                    "reason": str(exc),
                    "protocol": {"profile": profile},
                }
            except Exception as exc:
                cache[profile] = {
                    "status": "backend_error",
                    "value": None,
                    "reason": f"{type(exc).__name__}: {exc}",
                    "protocol": {"profile": profile},
                }
        results[metric] = _select(metric, cache[profile])
    return results


def pitch_metric(*, metric, reference, hypothesis, sample_rate=None, **inputs):
    """Public registry adapter; see evaluate_pitch for efficient multi-head calls."""
    return evaluate_pitch(
        [metric], reference=reference, hypothesis=hypothesis, sample_rate=sample_rate, **inputs
    )[metric]
