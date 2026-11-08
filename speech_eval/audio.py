"""Optional full-reference audio adapters. No hidden crop, gain fit or delay search."""

from importlib.metadata import version
import warnings


def waveform_metric(*, metric, reference, hypothesis, sample_rate, mixture=None):
    import numpy as np

    config = {
        "input_sample_rate": sample_rate,
        "mono": True,
        "length_policy": "strict_equal",
        "delay_alignment": "none",
        "gain_normalization": "none",
        "aggregation": "utterance_macro",
    }

    def failure(status, reason):
        return {
            "metric": metric,
            "status": status,
            "value": None,
            "reason": reason,
            "protocol": config,
        }

    if isinstance(sample_rate, bool) or not isinstance(sample_rate, int) or sample_rate <= 0:
        return failure("invalid_input", "sample_rate must be a positive integer")

    def array(value):
        from pathlib import Path

        if isinstance(value, (str, Path)):
            import soundfile as sf

            value, rate = sf.read(value, dtype="float64")
            if rate != sample_rate:
                raise ValueError(f"File sample rate {rate} != declared {sample_rate}")
        return np.asarray(value, dtype=np.float64)

    try:
        ref, hyp = array(reference), array(hypothesis)
    except (ValueError, OSError, RuntimeError) as exc:
        return failure("invalid_input", str(exc))
    if ref.ndim != 1 or hyp.ndim != 1 or ref.shape != hyp.shape or not ref.size:
        return failure("invalid_input", "require nonempty mono arrays with equal lengths")
    if not np.isfinite(ref).all() or not np.isfinite(hyp).all():
        return failure("invalid_input", "nonfinite waveform")
    if not np.any(ref):
        return failure("undefined_reference", "silent reference; no fabricated quality score")
    try:
        with warnings.catch_warnings(record=True) as messages:
            warnings.simplefilter("always")
            if metric in ("pesq_wb", "pesq_nb"):
                from pesq import pesq
                import soxr

                target = 16000 if metric == "pesq_wb" else 8000
                config.update(
                    scoring_sample_rate=target,
                    mode="wb" if target == 16000 else "nb",
                    resampler="soxr_HQ",
                )
                if sample_rate != target:
                    ref = soxr.resample(ref, sample_rate, target, quality="HQ")
                    hyp = soxr.resample(hyp, sample_rate, target, quality="HQ")
                value = pesq(target, ref, hyp, config["mode"])
                backend = {"pesq": version("pesq"), "soxr": version("soxr")}
            elif metric in ("stoi", "estoi"):
                from pystoi import stoi

                config.update(extended=metric == "estoi", internal_resampling="pystoi to 10kHz")
                value = stoi(ref, hyp, sample_rate, extended=metric == "estoi")
                backend = {"pystoi": version("pystoi")}
            elif metric in ("si_sdr", "si_sdri"):
                import fast_bss_eval

                config.update(zero_mean=True, permutation=False)
                value = float(
                    fast_bss_eval.si_sdr(
                        ref[None], hyp[None], zero_mean=True, return_perm=False
                    ).mean()
                )
                if metric == "si_sdri":
                    mix = array(mixture)
                    if mix.shape != ref.shape or not np.isfinite(mix).all():
                        return failure(
                            "invalid_input", "SI-SDRi requires same-length finite mixture"
                        )
                    value -= float(
                        fast_bss_eval.si_sdr(
                            ref[None], mix[None], zero_mean=True, return_perm=False
                        ).mean()
                    )
                backend = {"fast_bss_eval": version("fast-bss-eval")}
            else:
                raise ValueError(metric)
        if messages:
            return failure("backend_warning", "; ".join(str(w.message) for w in messages))
        if not np.isfinite(value):
            return failure("nonfinite_result", "upstream returned nonfinite value")
        return {
            "metric": metric,
            "status": "ok",
            "value": float(value),
            "backend": backend,
            "protocol": config,
        }
    except ImportError:
        raise
    except Exception as exc:
        return failure("backend_error", f"{type(exc).__name__}: {exc}")
