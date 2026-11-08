"""Echo energy reduction over explicitly annotated far-end-only regions."""

from pathlib import Path


def erle_metric(
    *, metric, reference, hypothesis, sample_rate, farend_only_regions, signal_definition
):
    import numpy as np

    protocol = {
        "profile": "erle-energy-v1",
        "sample_rate": sample_rate,
        "signal_definition": signal_definition,
        "scoring_region": "explicit_farend_single_talk",
        "gain_normalization": "none",
        "delay_alignment": "none",
        "resampling": "none",
        "aggregation": "10log10(sum_before_energy/sum_after_energy)",
        "sample_interval": "half-open; round(seconds * sample_rate)",
    }

    def fail(status, reason, details=None):
        return dict(
            metric=metric,
            status=status,
            value=None,
            value_unit="dB",
            reason=reason,
            protocol=protocol,
            details=details or {},
        )

    if isinstance(sample_rate, bool) or not isinstance(sample_rate, int) or sample_rate <= 0:
        return fail("invalid_input", "sample_rate must be a positive integer")
    if signal_definition not in ("isolated_echo", "microphone_farend_only"):
        return fail("invalid_input", "Declare isolated_echo or microphone_farend_only")

    def load(v):
        if isinstance(v, (str, Path)):
            import soundfile as sf

            v, rate = sf.read(v, dtype="float64")
            if rate != sample_rate:
                raise ValueError("File sample rate differs from declared rate")
        return np.asarray(v, dtype=np.float64)

    try:
        before, after = load(reference), load(hypothesis)
        if before.ndim != 1 or before.shape != after.shape or not before.size:
            raise ValueError("Require equal-length nonempty mono inputs")
        if not np.isfinite(before).all() or not np.isfinite(after).all():
            raise ValueError("Nonfinite waveform")
        if not isinstance(farend_only_regions, (list, tuple)) or not farend_only_regions:
            raise ValueError("At least one explicit far-end-only region is required")
        intervals = []
        for region in farend_only_regions:
            if len(region) != 2 or any(
                isinstance(v, bool) or not isinstance(v, (int, float)) or not np.isfinite(v)
                for v in region
            ):
                raise ValueError("Regions must be [start_seconds,end_seconds] pairs")
            start, end = region
            if not 0 <= start < end <= len(before) / sample_rate:
                raise ValueError("Regions must lie inside the recording")
            a, b = round(start * sample_rate), round(end * sample_rate)
            if a >= b:
                raise ValueError("Region is empty at sample resolution")
            intervals.append((a, b))
        intervals.sort()
        if any(b > c for (_, b), (c, _) in zip(intervals, intervals[1:])):
            raise ValueError("Overlapping regions would double-count samples")
        numerator = sum(float(np.dot(before[a:b], before[a:b])) for a, b in intervals)
        denominator = sum(float(np.dot(after[a:b], after[a:b])) for a, b in intervals)
        details = dict(
            before_energy=numerator,
            after_energy=denominator,
            scored_samples=sum(b - a for a, b in intervals),
            regions_samples=intervals,
        )
        if not np.isfinite(numerator) or not np.isfinite(denominator):
            return fail("invalid_input", "Energy overflow")
        if numerator <= 0:
            return fail(
                "undefined_reference", "No echo/input energy in the declared region", details
            )
        if denominator == 0:
            return fail(
                "infinite_result", "Zero residual energy: ERLE is +infinity; not clamped", details
            )
        value = 10 * (np.log10(numerator) - np.log10(denominator))
        return dict(
            metric=metric,
            status="ok",
            value=float(value),
            value_unit="dB",
            direction="higher_is_better",
            protocol=protocol,
            details=details,
        )
    except (ValueError, TypeError, OSError, RuntimeError) as exc:
        return fail("invalid_input", str(exc))
