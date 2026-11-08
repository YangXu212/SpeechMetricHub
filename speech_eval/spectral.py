"""Explicit spectral/cepstral profiles; no universal 'LSD' or 'MCD' default.

URGENT profiles follow the public challenge's mathematical definitions.
Mel-cepstral analysis and alignment are delegated to pysptk and fastdtw.
"""

from importlib.metadata import version
from pathlib import Path


def spectral_metric(*, metric, reference, hypothesis, sample_rate):
    import numpy as np

    protocol = dict(
        sample_rate=sample_rate,
        channel_policy="strict_mono",
        length_policy="strict_equal",
        resampling="none",
        delay_alignment="none",
        aggregation="utterance_macro",
        profile=metric,
    )

    def failure(status, reason):
        return dict(metric=metric, status=status, value=None, reason=reason, protocol=protocol)

    if isinstance(sample_rate, bool) or not isinstance(sample_rate, int) or sample_rate < 1000:
        return failure("invalid_input", "sample_rate must be an integer >= 1000")

    def load(value):
        if isinstance(value, (str, Path)):
            import soundfile as sf

            value, rate = sf.read(value, dtype="float64")
            if rate != sample_rate:
                raise ValueError("File rate differs from declared sample_rate")
        return np.asarray(value, dtype=np.float64)

    try:
        ref, hyp = load(reference), load(hypothesis)
        if ref.ndim != 1 or hyp.ndim != 1 or not ref.size or ref.shape != hyp.shape:
            raise ValueError("Require nonempty equal-length mono inputs; no implicit crop")
        if not np.isfinite(ref).all() or not np.isfinite(hyp).all():
            raise ValueError("Nonfinite waveform")
        if not np.any(ref) or not np.any(hyp):
            raise ValueError("Silent input is outside this speech spectral profile")
        frame = int(sample_rate * 0.032) if metric.startswith("lsd_") else 1024
        if len(ref) < frame:
            raise ValueError(f"At least {frame} samples are required")
    except (ValueError, OSError, RuntimeError, TypeError) as exc:
        return failure("invalid_input", str(exc))

    gain_fit = metric in ("lsd_urgent", "mcd_urgent")
    protocol["gain_normalization"] = (
        "least_squares_hypothesis_to_reference_eps1e-8" if gain_fit else "none"
    )
    if gain_fit:
        hyp = hyp * (np.dot(ref, hyp) / (np.dot(hyp, hyp) + 1e-8))
    backend = {"numpy": version("numpy")}
    try:
        if metric in ("lsd_urgent", "lsd_db"):
            import librosa

            hop = int(sample_rate * 0.016)
            protocol.update(
                n_fft=frame,
                hop_length=hop,
                window="hann_periodic",
                center=True,
                pad_mode="constant",
                frequency_bins="all_one_sided",
            )
            a, b = [
                np.abs(
                    librosa.stft(
                        x,
                        n_fft=frame,
                        hop_length=hop,
                        window="hann",
                        center=True,
                        pad_mode="constant",
                    )
                )
                for x in (ref, hyp)
            ]
            if metric == "lsd_urgent":
                delta = np.log(a**2 / (b + 1e-8) ** 2 + 1e-8)
                protocol.update(logarithm="natural log power ratio", epsilon=1e-8)
                unit = "natural_log_power_ratio"
            else:
                delta = 10 * np.log10(np.maximum(a**2, 1e-12)) - 10 * np.log10(
                    np.maximum(b**2, 1e-12)
                )
                protocol.update(logarithm="10*log10 power", power_floor=1e-12)
                unit = "dB"
            value = np.sqrt(np.mean(delta**2, axis=0)).mean()
            backend["librosa"] = version("librosa")
        elif metric in ("mcd_urgent", "mcd_dtw_c1"):
            import pysptk
            from fastdtw import fastdtw
            from scipy.spatial.distance import euclidean

            settings = {
                8000: (13, 0.31),
                16000: (23, 0.42),
                22050: (34, 0.45),
                24000: (34, 0.46),
                32000: (36, 0.50),
                44100: (39, 0.53),
                48000: (39, 0.55),
            }
            if sample_rate not in settings:
                return failure("invalid_input", "Unsupported SPTK sample rate")
            order, alpha = settings[sample_rate]
            start = 0 if metric == "mcd_urgent" else 1
            window = pysptk.sptk.hamming(1024)

            def features(x):
                return np.stack(
                    [
                        pysptk.mcep(x[i : i + 1024] * window, order, alpha, eps=1e-6, etype=1)[
                            start:
                        ]
                        for i in range(0, len(x) - 1024 + 1, 256)
                    ]
                )

            a, b = features(ref), features(hyp)
            _, path = fastdtw(a, b, radius=1, dist=euclidean)
            indices = np.asarray(path)
            delta = a[indices[:, 0]] - b[indices[:, 1]]
            value = (10 / np.log(10) * np.sqrt(2 * np.sum(delta**2, axis=1))).mean()
            protocol.update(
                n_fft=1024,
                hop_length=256,
                window="pysptk_hamming",
                center=False,
                padding=False,
                mcep_order=order,
                alpha=alpha,
                coefficient_start=start,
                mcep_epsilon=1e-6,
                mcep_etype=1,
                time_alignment="fastdtw_radius1_euclidean_on_selected_coefficients",
                waveform_scale="float64_original_amplitude",
                silence_removal=False,
            )
            unit = "dB"
            backend.update({p: version(p) for p in ("pysptk", "fastdtw", "scipy")})
        else:
            raise ValueError(f"Unknown spectral profile {metric}")
        if not np.isfinite(value):
            return failure("nonfinite_result", "Backend produced a nonfinite score")
        return dict(
            metric=metric,
            status="ok",
            value=float(value),
            value_unit=unit,
            direction="lower_is_better",
            protocol=protocol,
            backend=backend,
        )
    except ImportError:
        raise
    except Exception as exc:
        return failure("backend_error", f"{type(exc).__name__}: {exc}")
